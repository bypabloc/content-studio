import { readFileSync } from 'node:fs';
import type { Page } from '@playwright/test';

// La API local que la app llama (127.0.0.1, con token); aquí no hay server: page.route responde desde _api/.
export const API = 'http://127.0.0.1:9999';

export interface Call {
  method: string;
  path: string;
  search: string;
  body: unknown;
}

/** Una respuesta que no es JSON: el audio de una toma, que sirve `/files`. */
export interface Binary {
  contentType: string;
  body: Buffer;
}

/** Respuestas propias de una prueba: lo que devuelve (JSON o `Binary`) se usa; `undefined`, la respuesta por defecto. */
export type Replies = (call: Call) => unknown;

/** Una respuesta de error del server: el estado HTTP y el cuerpo JSON que devuelve (p. ej. un 422 con su código). */
export interface Failed {
  failed: { status: number; body: unknown };
}

function isBinary(reply: unknown): reply is Binary {
  return typeof reply === 'object' && reply !== null && Buffer.isBuffer((reply as Binary).body);
}

function isFailed(reply: unknown): reply is Failed {
  return typeof reply === 'object' && reply !== null && 'failed' in reply;
}

export function apiFixture<T = Record<string, unknown>>(name: string): T {
  return JSON.parse(readFileSync(new URL(`../_api/${name}.json`, import.meta.url), 'utf8')) as T;
}

function fixture(name: string): Record<string, unknown> {
  return apiFixture<Record<string, unknown>>(name);
}

/**
 * Abre la app como la abre Tauri: `get_connection` simulado (o fallando), el diálogo y los eventos de Tauri simulados, la
 * API servida por page.route y la navegación a la raíz. Devuelve las llamadas que la app hace a la API, para comprobar
 * los endpoints.
 */
export async function openApp(
  page: Page,
  options: { connect?: 'ok' | 'spawn_failed'; settings?: Record<string, unknown>; replies?: Replies } = {},
): Promise<{ calls: Call[] }> {
  await page.addInitScript((connect) => {
    // Los eventos de Tauri (soltar archivos) se registran aquí; `__emitEvent` los dispara como lo haría el sistema.
    const listeners: Record<string, number> = {};
    let nextId = 1;
    Object.defineProperty(window, '__TAURI_INTERNALS__', {
      value: {
        metadata: { currentWindow: { label: 'main' }, currentWebview: { label: 'main', windowLabel: 'main' } },
        transformCallback: (callback: (message: unknown) => void) => {
          const id = nextId++;
          Object.defineProperty(window, `_${id}`, { value: callback });
          return id;
        },
        invoke: async (command: string, args: { event?: string; handler?: number; options?: { multiple?: boolean } } = {}) => {
          if (command === 'get_connection') {
            if (connect === 'spawn_failed') throw 'server_spawn_failed';
            return { baseUrl: 'http://127.0.0.1:9999', token: 'tok' };
          }
          if (command === 'plugin:dialog|open') {
            const picked = (window as unknown as { __dialogPick?: string[] }).__dialogPick ?? null;
            // Con `multiple: false` el diálogo de Tauri devuelve una sola ruta, no una lista.
            return args.options?.multiple === false ? (picked?.[0] ?? null) : picked;
          }
          if (command === 'plugin:event|listen' && args.event !== undefined && args.handler !== undefined) {
            listeners[args.event] = args.handler;
          }
          return null;
        },
      },
    });
    Object.defineProperty(window, '__hasListener', { value: (event: string) => event in listeners });
    Object.defineProperty(window, '__emitEvent', {
      value: (event: string, payload: unknown) => {
        const callback = (window as unknown as Record<string, (message: unknown) => void>)[`_${listeners[event]}`];
        callback({ event, id: 0, payload });
      },
    });
  }, options.connect ?? 'ok');
  const calls = await mockApi(page, { ...fixture('settings'), ...options.settings }, options.replies);
  await page.goto('/');
  return { calls };
}

/** ¿Ya registró la app un listener del evento de Tauri (p. ej. `tauri://drag-drop`, al soltar archivos)? */
export function hasListener(page: Page, event: string): Promise<boolean> {
  return page.evaluate(
    (name) => (window as unknown as { __hasListener: (e: string) => boolean }).__hasListener(name),
    event,
  );
}

/** Dispara un evento de Tauri dentro de la página, como si el sistema lo emitiera (soltar archivos sobre la ventana). */
export function emitEvent(page: Page, event: string, payload: unknown): Promise<void> {
  return page.evaluate(
    ({ name, data }) => (window as unknown as { __emitEvent: (e: string, p: unknown) => void }).__emitEvent(name, data),
    { name: event, data: payload },
  );
}

/** Lo que devolverá el diálogo «Importar» (`plugin:dialog|open`): las rutas que el usuario elige. */
export function setDialogPick(page: Page, paths: string[]): Promise<void> {
  return page.evaluate((picked) => {
    (window as unknown as { __dialogPick: string[] }).__dialogPick = picked;
  }, paths);
}

/** Un cuerpo que no es JSON (la toma subida como WAV) queda en null: la prueba mira el camino, no el contenido. */
function parseBody(raw: string | null): unknown {
  try {
    return raw ? (JSON.parse(raw) as unknown) : null;
  } catch {
    return null;
  }
}

/** Responde la API desde las respuestas grabadas, con un estado mínimo (pausa y ajustes) que cambia con PUT y DELETE. */
export async function mockApi(page: Page, settings: Record<string, unknown>, replies?: Replies): Promise<Call[]> {
  const calls: Call[] = [];
  const store: Record<string, unknown> = { ...settings };
  let paused = false;
  const jobs = fixture('jobs') as unknown as unknown[];
  const engines = fixture('engines/list') as unknown as unknown[];
  const system = fixture('system/info');
  const storage = fixture('storage/paths');
  const corsHeaders = {
    'access-control-allow-origin': '*',
    'access-control-allow-methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'access-control-allow-headers': 'authorization,content-type',
  };

  await page.route(`${API}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const body = parseBody(request.postData());
    calls.push({ method: request.method(), path: url.pathname, search: url.search, body });
    const { method, pathname } = { method: request.method(), pathname: url.pathname };

    const custom = replies?.({ method, path: pathname, search: url.search, body });
    let reply: unknown = {};
    if (custom !== undefined) reply = custom;
    else if (method === 'GET' && pathname === '/jobs') reply = jobs;
    else if (method === 'GET' && pathname === '/engines') reply = engines;
    else if (method === 'GET' && pathname === '/system') reply = system;
    else if (method === 'GET' && pathname === '/storage') reply = storage;
    else if (method === 'GET' && pathname === '/queue') reply = { paused };
    else if (method === 'POST' && pathname === '/queue/pause') reply = { paused: (paused = true) };
    else if (method === 'POST' && pathname === '/queue/resume') reply = { paused: (paused = false) };
    else if (method === 'PUT' && pathname === '/queue/order') reply = { ids: (body as { ids: number[] }).ids };
    else if (method === 'POST' && /^\/jobs\/\d+\/cancel$/.test(pathname)) reply = { cancelled: true };
    else if (method === 'POST' && /^\/jobs\/\d+\/retry$/.test(pathname)) reply = { ...jobs[0], id: 5, status: 'queued' };
    else if (method === 'DELETE' && pathname === '/settings') {
      const prefix = url.searchParams.get('prefix') ?? '';
      const removed = Object.keys(store).filter((key) => key.startsWith(prefix));
      removed.forEach((key) => delete store[key]);
      reply = { deleted: removed.length };
    } else if (pathname.startsWith('/settings/')) {
      const key = decodeURIComponent(pathname.slice('/settings/'.length));
      if (method === 'PUT') store[key] = (body as { value: unknown }).value;
      reply = { key, value: store[key] ?? null };
    }

    if (isFailed(reply)) {
      await route.fulfill({ status: reply.failed.status, headers: corsHeaders, contentType: 'application/json', body: JSON.stringify(reply.failed.body) });
    } else if (isBinary(reply)) {
      await route.fulfill({ status: 200, headers: corsHeaders, contentType: reply.contentType, body: reply.body });
    } else {
      await route.fulfill({ status: 200, headers: corsHeaders, contentType: 'application/json', body: JSON.stringify(reply) });
    }
  });

  // Después del catch-all: Playwright usa la última ruta que coincide, así que el SSE gana sobre el resto.
  await page.route(`${API}/events**`, (route) =>
    route.fulfill({ status: 200, contentType: 'text/event-stream', body: ': ping\n\n' }),
  );
  return calls;
}

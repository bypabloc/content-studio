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

function fixture(name: string): Record<string, unknown> {
  return JSON.parse(readFileSync(new URL(`../_api/${name}.json`, import.meta.url), 'utf8')) as Record<string, unknown>;
}

/**
 * Abre la app como la abre Tauri: `get_connection` simulado (o fallando), la API servida por page.route y la
 * navegación a la raíz. Devuelve las llamadas que la app hace a la API, para comprobar los endpoints.
 */
export async function openApp(
  page: Page,
  options: { connect?: 'ok' | 'spawn_failed'; settings?: Record<string, unknown> } = {},
): Promise<{ calls: Call[] }> {
  await page.addInitScript((connect) => {
    Object.defineProperty(window, '__TAURI_INTERNALS__', {
      value: {
        metadata: { currentWindow: { label: 'main' }, currentWebview: { label: 'main', windowLabel: 'main' } },
        invoke: async (command: string) => {
          if (command === 'get_connection') {
            if (connect === 'spawn_failed') throw 'server_spawn_failed';
            return { baseUrl: 'http://127.0.0.1:9999', token: 'tok' };
          }
          return null;
        },
      },
    });
  }, options.connect ?? 'ok');
  const calls = await mockApi(page, { ...fixture('settings'), ...options.settings });
  await page.goto('/');
  return { calls };
}

/** Responde la API desde las respuestas grabadas, con un estado mínimo (pausa y ajustes) que cambia con PUT y DELETE. */
export async function mockApi(page: Page, settings: Record<string, unknown>): Promise<Call[]> {
  const calls: Call[] = [];
  const store: Record<string, unknown> = { ...settings };
  let paused = false;
  const jobs = fixture('jobs') as unknown as unknown[];

  await page.route(`${API}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const body = request.postData() ? (JSON.parse(request.postData() as string) as unknown) : null;
    calls.push({ method: request.method(), path: url.pathname, search: url.search, body });
    const { method, pathname } = { method: request.method(), pathname: url.pathname };

    let reply: unknown = {};
    if (method === 'GET' && pathname === '/jobs') reply = jobs;
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

    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(reply) });
  });

  // Después del catch-all: Playwright usa la última ruta que coincide, así que el SSE gana sobre el resto.
  await page.route(`${API}/events**`, (route) =>
    route.fulfill({ status: 200, contentType: 'text/event-stream', body: ': ping\n\n' }),
  );
  return calls;
}

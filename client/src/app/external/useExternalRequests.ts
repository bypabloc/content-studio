import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { useEffect } from 'react';

import type { Api } from '@/shared/api/client';
import { useApi } from '@/shared/api/context';
import { toast } from '@/shared/components/molecules/UIToast';
import { type MessageKey, t } from '@/shared/i18n/t';
import { setPrefill } from '@/shared/navigation/prefill';
import { openInEditor } from '@/shared/navigation/sendTo';

import { type ExternalRequest, type NewType, parseExternal, type SendAction } from './parseExternal';

/** El evento con el que Rust reenvía el argv de un segundo arranque (external.rs). */
export const EXTERNAL_EVENT = 'external-request';

/** El botón de cada sección con el que el usuario confirma lo valores del enlace (AC-3: nada se encola sin él). */
const ACTION_KEY: Record<NewType, MessageKey> = {
  narration: 'narration.generate',
  music: 'music.generate',
  'media.convert': 'convert.submit',
};

/** Qué trabajo encola cada acción de «Enviar a», con el valor por defecto de su pantalla (spec 031, AC-7). */
const SEND_JOB: Record<Exclude<SendAction, 'editor'>, (input: string) => { kind: string; params: Record<string, unknown> }> = {
  'convert-mp3': (input) => ({ kind: 'media.convert', params: { input, target: 'mp3', options: {} } }),
  normalize: (input) => ({ kind: 'media.normalize', params: { input, preset: 'youtube' } }),
  clean: (input) => ({
    kind: 'clean.analyze',
    params: { input, model: 'large-v3-turbo', language: 'es', min_gap: 0.5, padding: 0.15, edges: true, auto_render: true },
  }),
  transcribe: (input) => ({ kind: 'transcribe', params: { input, model: 'large-v3-turbo', language: 'auto' } }),
};

/**
 * Recibe los enlaces `content-studio://`, el «Enviar a» y los pedidos que llegan con la ventana abierta (spec 031).
 * Un enlace solo navega o rellena; «Enviar a» encola porque el usuario eligió la acción en el Explorador (AC-7).
 */
export function useExternalRequests(): void {
  const api = useApi();
  useEffect(() => {
    let active = true;
    let stop: (() => void) | undefined;
    // Fuera de Tauri (vite en el navegador) no hay evento: el error se ignora.
    Promise.resolve()
      .then(() => listen<string[]>(EXTERNAL_EVENT, (event) => handleArgv(event.payload, api)))
      .then((stopListening) => {
        if (active) stop = stopListening;
        else stopListening();
      })
      .catch(() => undefined);
    // El arranque en frío: el argv con el que se abrió el proceso.
    Promise.resolve()
      .then(() => invoke<string[]>('startup_argv'))
      .then((argv) => handleArgv(argv, api))
      .catch(() => undefined);
    return () => {
      active = false;
      stop?.();
    };
  }, [api]);
}

async function handleArgv(argv: string[], api: Api): Promise<void> {
  const request = parseExternal(argv);
  if (request === null) return;
  if (request.kind === 'error') return fail();
  if (request.kind === 'send') return send(request.action, request.paths, api);
  await apply(request);
}

async function apply(request: Exclude<ExternalRequest, { kind: 'send' }>): Promise<void> {
  switch (request.kind) {
    case 'open':
      return go(request.section);
    case 'job':
      setPrefill('library', { job: String(request.id) });
      return go('library');
    case 'library':
      setPrefill('library', { id: String(request.id) });
      return go('library');
    case 'new':
      return openNew(request.type, request.params);
  }
}

async function openNew(type: NewType, params: Record<string, string>): Promise<void> {
  if (type === 'media.convert') {
    const { input, ...rest } = params;
    // Una ruta que no existe no se rellena: el enlace no puede apuntar a archivos inventados (AC-4).
    if (input !== undefined && !(await exists(input))) return fail();
    setPrefill('convert', input === undefined ? rest : { path: input, ...rest });
  } else {
    setPrefill(type, params);
  }
  toast.info(t('deeplink.prefilled', { action: t(ACTION_KEY[type]) }));
  go(type === 'media.convert' ? 'convert' : type);
}

async function send(action: SendAction, paths: string[], api: Api): Promise<void> {
  const present: string[] = [];
  let skipped = 0;
  for (const path of paths) {
    if (await exists(path)) present.push(path);
    else skipped += 1;
  }
  if (action === 'editor') {
    if (present.length > 0) openInEditor(present);
  } else {
    let queued = 0;
    for (const input of present) {
      try {
        await api.post('/jobs', SEND_JOB[action](input));
        queued += 1;
      } catch (error) {
        toast.error(error instanceof Error ? error.message : t('api.unknown_error'));
      }
    }
    if (queued > 0) toast.info(t('sendto.queued', { count: String(queued) }));
  }
  if (skipped > 0) toast.info(t('sendto.skipped', { count: String(skipped) }));
}

async function exists(path: string): Promise<boolean> {
  return (await invoke<boolean>('path_exists', { path })) === true;
}

function go(section: string): void {
  window.location.hash = `/${section}`;
}

function fail(): void {
  toast.error(t('deeplink.invalid'));
}

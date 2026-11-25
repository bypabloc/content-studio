import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { useEffect } from 'react';

import { toast } from '@/shared/components/molecules/UIToast';
import { type MessageKey, t } from '@/shared/i18n/t';
import { setPrefill } from '@/shared/navigation/prefill';

import { type ExternalRequest, type NewType, parseExternal } from './parseExternal';

/** El evento con el que Rust reenvía el argv de un segundo arranque (external.rs). */
export const EXTERNAL_EVENT = 'external-request';

/** El botón de cada sección con el que el usuario confirma lo valores iniciales (AC-3: nada se encola sin él). */
const ACTION_KEY: Record<NewType, MessageKey> = {
  narration: 'narration.generate',
  music: 'music.generate',
  'media.convert': 'convert.submit',
};

/**
 * Recibe los enlaces `content-studio://` (AC-1, AC-2, AC-3, AC-4) y los pedidos que llegan con la ventana abierta (AC-5).
 * Nunca llama a la API: lo que llega por un enlace solo navega o rellena.
 */
export function useExternalRequests(): void {
  useEffect(() => {
    let active = true;
    let stop: (() => void) | undefined;
    // Fuera de Tauri (vite en el navegador) no hay evento: el error se ignora.
    Promise.resolve()
      .then(() => listen<string[]>(EXTERNAL_EVENT, (event) => handleArgv(event.payload)))
      .then((stopListening) => {
        if (active) stop = stopListening;
        else stopListening();
      })
      .catch(() => undefined);
    // El arranque en frío: el argv con el que se abrió el proceso.
    Promise.resolve()
      .then(() => invoke<string[]>('startup_argv'))
      .then((argv) => handleArgv(argv))
      .catch(() => undefined);
    return () => {
      active = false;
      stop?.();
    };
  }, []);
}

async function handleArgv(argv: string[]): Promise<void> {
  const request = parseExternal(argv);
  if (request === null) return;
  if (request.kind === 'error') return fail();
  await apply(request);
}

async function apply(request: Exclude<ExternalRequest, { kind: 'error' }>): Promise<void> {
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
    if (input !== undefined && !(await invoke<boolean>('path_exists', { path: input }))) return fail();
    setPrefill('convert', input === undefined ? rest : { path: input, ...rest });
  } else {
    setPrefill(type, params);
  }
  toast.info(t('deeplink.prefilled', { action: t(ACTION_KEY[type]) }));
  go(type === 'media.convert' ? 'convert' : type);
}

function go(section: string): void {
  window.location.hash = `/${section}`;
}

function fail(): void {
  toast.error(t('deeplink.invalid'));
}

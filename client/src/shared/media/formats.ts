import { hasMessage, type MessageKey, t } from '@/shared/i18n/t';

/** Extensiones de audio y video que aceptan Convertir y Normalizar (las mismas que lee el server). */
export const MEDIA_EXTENSIONS = ['wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac', 'mp4', 'mov', 'mkv', 'webm', 'avi', 'm4v'];

const VIDEO_EXTENSIONS = ['mp4', 'mov', 'mkv', 'webm', 'avi', 'm4v'];

/** ¿Es un video (su extensión)? Un audio o una extensión desconocida no lo son. */
export function isVideoPath(path: string): boolean {
  return VIDEO_EXTENSIONS.includes(/\.([^./\\]+)$/.exec(path)?.[1]?.toLowerCase() ?? '');
}

/** El nombre del archivo, sin su carpeta. */
export function baseName(path: string): string {
  return path.split(/[\\/]/).pop() ?? path;
}

/**
 * El motivo de un trabajo con error, en el idioma activo. El server da un código (`error.<código>`); si el catálogo no
 * tiene un texto sin parámetros para ese código, se dice el error genérico, en vez de mostrar una llave sin rellenar.
 */
export function jobErrorMessage(code: string | null | undefined): string {
  const key = `error.${code ?? ''}`;
  if (code && hasMessage(key)) {
    const text = t(key as MessageKey);
    if (!text.includes('{')) return text;
  }
  return t('media.error.generic');
}

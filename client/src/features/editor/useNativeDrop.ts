import { useFilePaths } from '@/shared/hooks/useFilePaths';

const MEDIA_EXTENSIONS = ['wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac', 'mp4', 'mov', 'mkv', 'webm', 'avi', 'm4v'];

/** Diálogo nativo y rutas de archivos soltados desde Windows para el editor. */
export function useNativeDrop(onPaths: (paths: string[]) => void) {
  return useFilePaths({ extensions: MEDIA_EXTENSIONS, onPaths });
}

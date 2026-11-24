/**
 * Un `<video>` o un `<audio>` sin controles propios: la revisión del Limpiador los maneja con su botón y su onda
 * (spec 013, D-6). `mediaRef` recibe el elemento para seguirlo con `useSyncedMedia`.
 */
export function UIMedia({
  kind,
  src,
  className,
  mediaRef,
  controls = false,
  label,
}: {
  kind: 'video' | 'audio';
  src: string;
  className?: string;
  mediaRef?: (element: HTMLMediaElement | null) => void;
  /** Los controles del sistema (la vista previa de la Biblioteca); la revisión del Limpiador usa los suyos. */
  controls?: boolean;
  label?: string;
}): React.JSX.Element {
  if (kind === 'video') return <video ref={mediaRef} src={src} className={className} controls={controls} aria-label={label} />;
  return <audio ref={mediaRef} src={src} className={className} controls={controls} aria-label={label} />;
}

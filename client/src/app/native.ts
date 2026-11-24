/**
 * Sensación de app nativa (D-8): el menú contextual del navegador no sale en la ventana. Solo sale donde una pantalla
 * lo marca con `data-allow-context`.
 */
export function blockContextMenu(event: MouseEvent): void {
  if (event.target instanceof Element && event.target.closest('[data-allow-context]')) return;
  // Los campos de texto conservan su menú (copiar, pegar y seleccionar todo).
  if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;
  event.preventDefault();
}

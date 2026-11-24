/** Los parámetros del hash de la sección actual (`#/mix?voice=…` da `voice`). Lo lee `useSectionId` para la sección. */
export function hashParams(): URLSearchParams {
  return new URLSearchParams(window.location.hash.split('?')[1] ?? '');
}

/** Abre una sección con parámetros en el hash, por ejemplo `openSection('mix', { voice })` (spec 016, D-4). */
export function openSection(section: string, params: Record<string, string>): void {
  window.location.hash = `/${section}?${new URLSearchParams(params).toString()}`;
}

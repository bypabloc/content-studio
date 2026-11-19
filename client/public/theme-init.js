// Antes de montar React: pone la clase dark con la caché para que no haya parpadeo (D-4). Es un espejo de
// readCachedTheme y resolveTheme en src/shared/theme/theme.ts; va como archivo porque la CSP no admite scripts inline.
(function () {
  try {
    var mode = localStorage.getItem('ui.theme');
    var dark = mode === 'dark' || (mode !== 'light' && matchMedia('(prefers-color-scheme: dark)').matches);
    if (dark) document.documentElement.classList.add('dark');
  } catch (error) {
    // Sin almacenamiento, la app arranca con el tema del sistema.
  }
})();

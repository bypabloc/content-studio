# 008: UIAppShell reemplaza al Shell y a la Sidebar

- **Contexto**: la app tenía su propia `Sidebar`, su `ThemeToggle` y un `Shell` que los juntaba. La sidebar colapsable de shadcn ya resuelve el colapsado a iconos.
- **Elegida** (D-7):
  - `UIAppShell` (organismo) recibe `nav` (grupos e ítems con `id`, `label` e `icon`), `active`, `footer` (tema y versión) y `aside` (el panel de la cola).
  - La barra colapsa a iconos con tooltips, con el botón o con `Ctrl+B`. El estado se guarda en el setting `ui.sidebar.collapsed`, que lee `app/Shell.tsx` con `useSetting`.
  - `app/Shell.tsx` compone `UIAppShell` con `NAV`. `app/Sidebar.tsx`, `app/ThemeToggle.tsx` y sus tests se borraron en la T5.
  - El modo móvil de la barra queda deshabilitado: Tauri fija `minWidth: 960` en `tauri.conf.json`.
- **Desvío**: la cola no va a la derecha, como dice AC-7, sino bajo las secciones de la barra. Ver [008-appshell-cola-bajo-secciones](008-appshell-cola-bajo-secciones.md).
- **Descartadas**: mantener una sidebar propia. Duplicaría el colapsado y el atajo.
- **Cómo revertir**: restaurar `app/Sidebar.tsx`, `app/ThemeToggle.tsx` y el `Shell.tsx` anterior desde `c2b0611`, y quitar `UIAppShell`.
- **Cómo comprobarla**: `tests/e2e/shell/happy-sidebar-collapse.e2e.ts` (AC-7): el botón y `Ctrl+B` colapsan la barra, y sigue colapsada al recargar. Corre con `python -m devtools test-runner --type=e2e`.
- **Antes de**: el merge a `dev`.

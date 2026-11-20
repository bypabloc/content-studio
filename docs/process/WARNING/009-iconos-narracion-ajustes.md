# 009: iconos en Narración y Ajustes, y el criterio de solo ícono

- **Contexto**: D-5 pide iconos en Narración (reproducir, comparar, regenerar, estrella, abrir carpeta e importar guion), «Generar» con icono y texto, y el selector de tema de Ajustes con un icono por opción. Tres puntos no quedan fijados: «abrir carpeta» no tiene botón en la app hoy (D-5 dice «a lo que existe al ejecutar»); la barra colapsable usa el `SidebarTrigger` de shadcn, sin tooltip y sin `useSidebar` exportado; y `UISelect` no mostraba íconos en sus opciones.
- **Elegida**:
  - Solo ícono con `UIIconButton`: reproducir y pausar (`Player`), comparar y regenerar (`NarrationResult`), elegir con estrella (`CompareTakes`; la toma elegida muestra la estrella llena junto a «Elegida») e importar guion (`ScriptEditor`). Sus nombres viven en `action.*`: se suman `play`, `choose`, `compare`, `regenerate` e `import`, y `pause` se reutiliza. Salen de los tres catálogos `player.play`, `player.pause`, `narration.compare.open`, `narration.compare.choose`, `narration.import.button` y `narration.result.regenerate`.
  - «Generar» conserva su texto y gana el ícono `narration`, el de su sección. «Restablecer elecciones» conserva su texto y gana `history`.
  - `UISelect` y `Picker` aceptan `icon` por opción. El selector de tema de Ajustes lo usa con `THEME_ICONS`, que se define una sola vez; el campo cerrado sigue mostrando el texto.
  - Colapsar la barra: el `SidebarTrigger` se envuelve en `UITooltip` con su misma etiqueta. Queda igual que un `UIIconButton` (solo ícono, tooltip y nombre accesible), y no se edita `shadcn/`.
- **Descartadas**:
  - `UIIconButton` para la barra: haría falta exportar `useSidebar` de `shadcn/sidebar.tsx`, que es código de proveedor.
  - `play` como ícono de «Generar»: se confundiría con reproducir.
  - Dejar «Elegir» como texto: D-4 pide solo ícono para una acción que se repite en cada toma.
  - Crear ya un botón «Abrir carpeta»: ninguna pantalla muestra hoy una carpeta de salida, y eso sería una función nueva (queda en PENDING).
- **Cómo revertir**: el commit `feat: iconos en Narración y Ajustes; criterio de solo icono en ui-components` deja cada cambio en su archivo. Revertirlo devuelve las claves `player.*`, `narration.compare.*`, `narration.import.button` y `narration.result.regenerate`.
- **Cómo comprobarla**: `bunx vitest run` en `client/` (`Player`, `CompareTakes`, `NarrationResult`, `NarrationPage`, `ScriptEditor` y `SettingsPage`) y `python -m devtools test-runner --type=e2e` (`happy-icons-tooltips`, `happy-apariencia-axe` y `happy-sidebar-collapse`).
- **Pendiente**: [PENDING/009-abrir-carpeta](../PENDING/009-abrir-carpeta.md). La mirada visual de Narración y Ajustes en la app real va con [PENDING/008-revision-visual-organismos](../PENDING/008-revision-visual-organismos.md).

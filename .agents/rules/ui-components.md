---
trigger: model_decision
description: Componentes de UI del client: textos en es.json, selectores con recomendado, tema, accesibilidad y atajos
---

# Componentes de UI (client/)

* **Textos**: cada texto visible sale del catálogo `server/src/content_studio/messages/{es,en,pt}.json` con `t('clave', parámetros)` (`shared/i18n/t.ts`), en el idioma activo. Un parámetro va entre llaves: `"theme.change": "Cambiar tema: {mode}"`. La clave es inglés con puntos (`queue.announce.picked`); una clave nueva va en los tres idiomas.
* **Nombre accesible**: el nombre de cada control contiene su texto visible (WCAG 2.5.3). El botón de tema dice «Cambiar tema: Claro», no solo «Cambiar tema». Axe no puede tener fallos serios en el shell, la cola ni Ajustes (`tests/e2e/shell/happy-apariencia-axe.e2e.ts`).
* **Selectores con recomendado**: `<RecommendedSelect>` (`shared/components/RecommendedSelect.tsx`) recibe `settingKey`, `label`, `options` (`{value, label, recommended?, disabled?, hint?}`) y `onChange`. Sin elección guardada, o si la guardada ya no existe, vale la recomendada, que lleva ★ en su
  texto y `t('select.recommended')` como tooltip. Cada cambio hace `PUT /settings/<clave>`. Las claves de los selectores empiezan por `select.`: «Restablecer elecciones» borra ese prefijo (`DELETE /settings?prefix=select.`) y deja `ui.*` y `notify.*`.
* **Tema**: `ui.theme` se guarda en `settings`; `shared/theme/` aplica la clase `dark` en `<html>`, y `public/theme-init.js` lo hace antes de montar React para que no parpadee. Los colores son tokens de `client/src/index.css` (`@theme inline`); no se escriben colores sueltos en los componentes.
* **Atajos**: `useShortcut('mod+k', handler)` (`shared/hooks/useShortcut.ts`). Ctrl+K abre la paleta; las demás (Ctrl+Enter, Espacio) las registra cada sección con el mismo hook. Ajustes lista los atajos.
* **Confirmaciones**: `window.confirm` para lo que borra datos (Restablecer elecciones). Sin diálogos propios hasta que una spec lo pida.
* **Componentes de shadcn**: se copian a `client/src/components/ui/` solo cuando una feature los usa. Hoy no hay ninguno: los controles son HTML con clases de Tailwind.
* **Tamaño**: un componente que pasa de 300 líneas se divide (`frontend-stack.md`).

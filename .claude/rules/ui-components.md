---
paths:
  - "client/**"
---

# Componentes de UI (client/)

Los componentes viven en `client/src/shared/components/` en cinco carpetas: `shadcn/` (código copiado de shadcn v4 sobre Base UI, no se edita a mano), `atoms/`, `molecules/` y `organisms/` (spec 008, D-3 y D-4).

## Jerarquía (D-4)

| Carpeta | Etiquetas nativas | Puede importar |
| :--- | :--- | :--- |
| `shadcn/` | Sí | npm, `shared/lib/` |
| `atoms/` | Sí | `shadcn/`, npm, `shared/lib/`, `shared/hooks/`, `shared/i18n/`, otros átomos |
| `molecules/` | No | Lo anterior y otras moléculas |
| `organisms/` | No | Lo anterior y otros organismos |
| `features/` y `app/` | No | `atoms/`, `molecules/` y `organisms/` (no `UIBox`), y el resto de `shared/` (`api`, `hooks`, `i18n`, `theme`, `notify`, `forms`). `app/` puede importar `features/` |

* Las pantallas arman su layout con `UIStack` (`direction`, `align`, `justify`), `UIGrid`, `UICard`, `UIPage` y `UIText`. `UIBox` es el contenedor de moléculas y organismos.
* Nadie fuera de `shared/components/` importa `shadcn/`, `@base-ui/react`, `lucide-react`, `recharts` ni `sonner`. `shared/` no importa `features/` ni `app/`.
* Lo hace cumplir oxlint con `no-restricted-imports` en `client/.oxlintrc.json`: un `override` por carpeta, sin solapamientos (oxlint fusiona mal las reglas repetidas). `client-lint` lo corre.
* Las etiquetas nativas (`div`, `button`, `input`, `img`, `output`…) solo van en átomos y en shadcn. La etapa `ui-structure` lo comprueba con el AST de TypeScript (`python -m devtools test-runner --type=ui-structure`). No hay marcador para excepciones.
* Lo que falte se agrega como componente en su nivel, nunca con una etiqueta en la pantalla: un `<time>` es el átomo `UITime`; un `<output>`, `UIBox role="status"`; un grupo con título, `UIBox role="group"` con `aria-labelledby`.
* Un componente que pasa de 300 líneas se divide por responsabilidad (`frontend-stack.md`).

## Textos

* Cada texto visible sale del catálogo `server/src/content_studio/messages/{es,en,pt}.json` con `t('clave', parámetros)` (`shared/i18n/t.ts`), en el idioma activo. Los parámetros van entre llaves: `"theme.change": "{mode}: cambiar a {next}"`.
* Las claves tienen la misma forma en los tres idiomas. La etapa `i18n` falla si falta una.

## Nombre accesible

* El nombre de cada control contiene su texto visible (WCAG 2.5.3). El botón de tema dice «Cambiar tema: Claro», nunca «Cambiar tema» a secas.
* Axe no puede tener fallos serios en el shell, la cola ni los ajustes (`tests/e2e/shell/happy-apariencia-axe.e2e.ts`).

## Botones de solo ícono (spec 009, D-4)

* **Solo ícono** (`UIIconButton`, con `label`): las acciones obvias y repetidas, como tema, cerrar, reproducir y pausar, detener, grabar, abrir carpeta, reintentar, cancelar un trabajo, quitar o borrar un ítem, copiar, estrella, asa de arrastre, comparar, regenerar, importar guion y colapsar la barra o la cola.
* **Ícono y texto** (`UIButton` con `icon`): los ítems de navegación (con la barra colapsada queda el ícono, y el nombre pasa al tooltip), los botones primarios de cada sección («Generar», «Exportar», «Construir») y las confirmaciones destructivas.
* **Solo texto**: etiquetas de campos, enlaces dentro de un párrafo, opciones de selectores y las acciones sin ícono obvio.
* El nombre accesible de un botón de solo ícono es su `label` (su `aria-label`), y el tooltip dice lo mismo. Las etiquetas viven una sola vez en `action.*` del catálogo, y varias pantallas las reutilizan.
* Un conmutador usa `aria-pressed` o cambia su etiqueta, nunca solo el ícono.
* Los íconos salen del mapa de `UIIcon` (tipo `IconName`): un nombre fuera del mapa no compila.
* `tests/e2e/shell/happy-icons-tooltips.e2e.ts` recorre los botones de solo ícono con el teclado y comprueba su tooltip.

## Selectores con recomendado

* `UIRecommendedSelect` (molécula, sobre `UISelect`) recuerda la última elección en `settings` bajo `select.<clave>`. Sin elección guardada, o si la guardada ya no existe, vale la recomendada, marcada con ★ (`select.recommended`).
* `beforeChange` deja cambiar solo si responde que sí (la licencia de un motor no comercial).
* «Restablecer elecciones» borra el prefijo `select.` (`DELETE /settings?prefix=select.`) y deja `ui.*` y `notify.*`.
* En e2e se elige una opción con `pickOption` (`tests/e2e/support/select.ts`): se abre el combobox por su nombre y se pulsa la opción. No hay `selectOption`: el selector no es un `<select>` nativo.

## Diálogos y confirmaciones

* `UIDialog` (organismo) para los diálogos modales: el título es su nombre accesible, el cierre lleva nombre (`closeLabel`) y Escape cierra. Ejemplo: el aviso de licencia (`features/narration/LicenseDialog.tsx`).
* `window.confirm` para lo que borra datos (Restablecer elecciones, en `features/settings`). El e2e lo acepta con `page.on('dialog')`.

## Tema

* `ui.theme` (claro, oscuro o sistema) vive en `settings`. `shared/theme/useTheme.ts` pone la clase `dark` en `<html>`, y `public/theme-init.js` lo hace antes de montar React para que no parpadee.
* Los colores son tokens de `client/src/styles/tokens.css` (claro y oscuro); no se escriben valores sueltos en las pantallas.

## Atajos

* `useShortcut('mod+k', handler)` (`shared/hooks/useShortcut.ts`). Ctrl+K busca una sección, Ctrl+B pliega la barra, Ctrl+Enter genera y Espacio reproduce o pausa. Ajustes lista los atajos.

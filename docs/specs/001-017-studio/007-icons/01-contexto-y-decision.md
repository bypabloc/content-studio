# 007: contexto y decisión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

## 1. Precondición

La 006 está fusionada: `git show origin/dev:client/src/features/narration/NarrationPage.tsx` existe.

## 2. Contexto

* El client no tiene librería de iconos: [ThemeToggle.tsx](../../../../client/src/app/ThemeToggle.tsx) muestra la palabra «Claro», «Oscuro» o «Sistema» en un botón con borde, y la cola, Ajustes y Narración usan solo texto en sus acciones.
* No hay componentes de shadcn copiados (`PENDING/005-desvios-d1-d8`, punto 1): los controles son HTML con Tailwind. [ui-components.md](../../../../.agents/rules/ui-components.md) exige que el nombre accesible contenga el texto visible (WCAG 2.5.3) y que axe no tenga fallos serios (`tests/e2e/shell/happy-apariencia-axe.e2e.ts`).
* Investigación del 2026-11-19 (agente `researcher` y `npm view`): lucide-react es ISC, declara peer `react ^16.5.1 || … || ^19.0.0`, publica casi a diario (1.70.0 el 2026-11-06 … 1.76.0 el 2026-11-19) y es el set que shadcn usa por defecto. @tabler/icons-react (MIT, más de 6500 iconos) y @phosphor-icons/react (MIT, 6 pesos) son alternativas válidas. Heroicons es pobre para audio y video, react-icons mezcla licencias por set (Font Awesome es CC BY 4.0) e Iconify pide su API salvo que se carguen colecciones a mano.
* Las secciones que vienen (Voces, Música, Limpiador, Subtítulos y sobre todo el Editor de las 015–017) necesitan muchos iconos de transporte y de edición: play, pausa, grabar, tijera, imán, capas, keyframe, volumen, silencio, carpeta.

## 3. Solución

Cada decisión pasó la escalera de `plan-format.md` §0:

* **D-1: lucide-react**, fijado con versión exacta (sin `^`) en `client/package.json`: la última publicada con al menos 14 días de antigüedad al ejecutar, para no adoptar una versión que el registro pueda retirar. Se importa por icono (`import { Sun } from 'lucide-react'`), así que el bundle solo suma los usados. Antes de fijar se comprueba que existan los nombres que pide el mapa de D-2; si falta uno de edición, se dibuja con otro de lucide (por ejemplo `Diamond` para keyframe) y no se suma una segunda librería. Descartadas: Tabler y Phosphor (buenas, pero apartarse de shadcn obliga a cambiar los iconos cada vez que se copie un componente), Heroicons (pocos iconos de audio), react-icons (licencia por set) e Iconify (descarga por API o carga manual de colecciones).
* **D-2: mapa semántico** `client/src/shared/icons.ts`: `export const ICONS = { themeLight: Sun, themeDark: Moon, themeSystem: Monitor, play: Play, pause: Pause, stop: Square, record: Circle, close: X, remove: Trash2, retry: RotateCcw, cancel: CircleX, openFolder: FolderOpen, star: Star, dragHandle: GripVertical, sidebarCollapse: PanelLeftClose, sidebarExpand: PanelLeftOpen, settings: Settings, narration: AudioLines, queue: ListOrdered, search: Search, copy: Copy, compare: GitCompare, regenerate: RefreshCw, importFile: FileUp, … }`. Cada acción tiene un nombre semántico y un solo icono en toda la app (regla de textos: «un texto repetido se define una vez»). `client/.oxlintrc.json` agrega `no-restricted-imports` de `lucide-react` en todo `src/` salvo `shared/icons.ts`. Descartado: importar lucide en cada componente (la misma acción terminaría con dos iconos distintos).
* **D-3: `IconButton`** (`client/src/shared/components/IconButton.tsx`) con las props `icon` (clave de `ICONS`), `label` (texto ya traducido con `t()`), `onClick`, `pressed?` (agrega `aria-pressed`), `shortcut?` (se muestra en el tooltip: «Reproducir (Espacio)»), `variant?` (`ghost` por defecto, `danger`) y `size?` (`sm` 28 px, `md` 32 px; el objetivo mínimo es de 24 px, WCAG 2.5.8). Renderiza un `<button>` con `aria-label={label}`, el icono con `aria-hidden="true"` y un `Tooltip` propio (`shared/components/Tooltip.tsx`) que aparece con hover tras 400 ms y de inmediato con `:focus-visible`, se cierra con Escape y se asocia por `aria-describedby` solo si agrega el atajo. El tooltip es CSS y un estado mínimo, posicionado arriba y corrido dentro de la ventana. Descartado: `@radix-ui/react-tooltip` (dependencia nueva para un único comportamiento que se resuelve en ~60 líneas; si una spec necesita popovers complejos, se reevalúa). También existe `Icon` (solo el icono, `aria-hidden`) para acompañar texto en botones e ítems.
* **D-4: criterio de uso**, escrito en `ui-components.md`:
  * **Solo icono** (con `IconButton`): acciones obvias y repetidas: tema, cerrar, reproducir y pausar, detener, grabar, abrir carpeta, reintentar, cancelar un trabajo, quitar o borrar un ítem, copiar, estrella, asa de arrastre y colapsar la sidebar.
  * **Icono y texto**: los ítems de navegación (con la sidebar colapsada queda el icono y el nombre pasa al tooltip), los botones primarios de cada sección («Generar», «Exportar», «Construir») y las confirmaciones destructivas.
  * **Solo texto**: etiquetas de campos, enlaces dentro de un párrafo y opciones de selectores.
  * El nombre accesible de un botón de solo icono es su `aria-label` y el tooltip muestra el mismo texto; un conmutador usa `aria-pressed` o cambia su etiqueta, nunca solo el icono.
* **D-5: aplicación** a lo que existe al ejecutar:
  * **ThemeToggle**: `IconButton` con el icono del modo actual (sol, luna o monitor) y la etiqueta `theme.change` («Cambiar tema: Claro. Siguiente: Oscuro»). El selector de Ajustes muestra el icono junto a cada opción.
  * **Sidebar**: cada entrada de `NAV` gana `icon` (clave de `ICONS`). Botón para colapsarla al pie; el estado queda en `settings` como `ui.sidebar.collapsed`, y colapsada mide 56 px con solo iconos y tooltips.
  * **Cola** (`JobRow`, `QueuePanel`): cancelar, reintentar, abrir carpeta, estrella y asa de arrastre con `IconButton`; el estado del trabajo gana un icono junto a su texto (en cola, corriendo con giro, listo, error).
  * **Paleta** (`CommandPalette`): el icono de la sección o la acción a la izquierda de cada resultado.
  * **Narración** (006): reproducir, comparar, regenerar, estrella, abrir carpeta e importar guion. «Generar» queda con icono y texto.
  * **Ajustes**: el icono en el selector de tema y en «Restablecer elecciones» (con texto).
* **D-6: catálogo**: las etiquetas nuevas de los botones de solo icono van a `client/messages/es.json` (`action.play`, `action.open_folder`, `sidebar.collapse`, …) y se definen una vez; varias pantallas reutilizan `action.*`.

## 4. Fuera de alcance

* Iconos propios o un set dibujado para la marca, y el icono de la app de Tauri (es del instalador, 020).
* Copiar componentes de shadcn que ninguna feature pide todavía (Tooltip de Radix, DropdownMenu).
* Animaciones de iconos más allá del giro del estado «corriendo».
* Rediseñar la disposición de las pantallas: solo cambian los botones e ítems que pasan a icono.

## 5. Criterios de aceptación

* **AC-1**: WHEN se renderiza `IconButton` con `label="Reproducir"` y `shortcut="Espacio"` THEN el botón tiene `aria-label="Reproducir"`, el svg tiene `aria-hidden="true"`, y al enfocarlo con teclado aparece el tooltip «Reproducir (Espacio)», que se cierra con Escape. Con `pressed`, el botón tiene `aria-pressed="true"`. Lo verifica: `shared/components/IconButton.test.tsx`.
* **AC-2**: WHEN el tema está en `light`, `dark` o `system` THEN ThemeToggle muestra el icono `themeLight`, `themeDark` o `themeSystem` (sin la palabra visible), su nombre accesible dice el modo actual y el siguiente, y al pulsarlo pasa al siguiente. Lo verifica: `app/ThemeToggle.test.tsx`.
* **AC-3**: WHEN se colapsa la sidebar THEN mide 56 px, cada ítem muestra solo el icono con su nombre en el tooltip y en `aria-label`, y al recargar sigue colapsada (`ui.sidebar.collapsed`). Lo verifica: `app/Sidebar.test.tsx` y el e2e `shell/happy-sidebar-collapse.e2e.ts`.
* **AC-4**: WHEN un archivo fuera de `shared/icons.ts` importa `lucide-react` THEN la etapa `client-lint` de `test-runner` falla con la regla `no-restricted-imports`. Lo verifica: un caso en `devtools/tests/unit/test_runner/` que corre oxlint sobre una fixture con ese import.
* **AC-5**: WHEN se abren el shell, la cola con un trabajo de cada estado, Ajustes y Narración, en claro y en oscuro THEN axe no reporta fallos serios ni críticos (`button-name` incluido) y cada botón de solo icono tiene un tooltip. Lo verifica: `tests/e2e/shell/happy-apariencia-axe.e2e.ts` ampliado y `tests/e2e/shell/happy-icons-tooltips.e2e.ts`.
* **AC-6**: WHEN se construye el client THEN el budget no crece más de 20 KB gzip respecto del baseline de la 006, y solo los iconos importados en `ICONS` llegan al bundle. Lo verifica: `python -m devtools test-runner --type=budget`.

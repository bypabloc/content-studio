# 009: contexto y decisión

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

## 1. Precondición

La 008 está fusionada: `git show origin/dev:client/src/shared/components/molecules/UIIconButton/index.tsx` existe.

## 2. Contexto

* La 008 trae `UIIcon`, con el mapa de nombres de klinikae sin los iconos de la clínica, más los del shell. También trae `UIIconButton` (`aria-label`, `aria-pressed` y tooltip), `UITooltip` (hover con demora, foco inmediato, Escape y atajo) y `UIAppShell`, con la sidebar colapsable a iconos y `ui.sidebar.collapsed`.
* Lo que falta es aplicar los iconos. `UIThemeToggle` de klinikae ya usa icono, pero la cola, la paleta, Narración y Ajustes todavía muestran texto en sus acciones, y no hay un criterio escrito de cuándo un botón va solo con icono.
* [ui-components.md](../../../../.agents/rules/ui-components.md) exige que el nombre accesible contenga el texto visible (WCAG 2.5.3) y que axe no tenga fallos serios (`tests/e2e/shell/happy-apariencia-axe.e2e.ts`).
* Las secciones que vienen (Voces, Música, Limpiador, Subtítulos y sobre todo el Editor de las 017–019) necesitan muchos iconos de transporte y de edición: play, pausa, grabar, tijera, imán, capas, keyframe, volumen, silencio, carpeta.
* Investigación del 2026-11-19 (agente `researcher` y `npm view`): lucide-react es ISC y es el set de shadcn. Tabler, Phosphor, Heroicons, react-icons e Iconify quedaron descartados, y con la 008 lucide queda fijado por klinikae.

## 3. Solución

Cada decisión pasó la escalera de `plan-format.md` §0:

* **D-1: sin piezas nuevas.** Todo sale de la 008. Si falta algo genérico (por ejemplo, un `UIIconToggleGroup`), se agrega como componente en su nivel, con su test, y no en la pantalla.
* **D-2: mapa de `UIIcon`.** Se suman los nombres en kebab-case que pide content-studio:
  * Transporte: `play`, `pause`, `stop`, `record`, `volume`, `mute`.
  * Tema: `theme-light`, `theme-dark`, `theme-system`.
  * Acciones: `close`, `remove`, `retry`, `cancel`, `open-folder`, `star`, `drag-handle`, `copy`, `compare`, `regenerate`, `import-file`, `settings`, `search`.
  * Secciones: `narration`, `queue`, `music`, `voices`, `editor`, `scissors`, `magnet`, `layers`, `keyframe`.
  * Cada acción tiene un solo icono en toda la app, igual que en la regla de textos, donde un texto repetido se define una vez.
  * Si un nombre no existe en la versión de lucide que fijó la 008, se usa el más cercano (por ejemplo, `Diamond` para keyframe) y se anota en `WARNING/009-iconos-sustitutos`. No se suma una segunda librería.
* **D-4: criterio de uso**, escrito en `ui-components.md`:
  * **Solo icono** (con `UIIconButton`): acciones obvias y repetidas, como tema, cerrar, reproducir y pausar, detener, grabar, abrir carpeta, reintentar, cancelar un trabajo, quitar o borrar un ítem, copiar, estrella, asa de arrastre y colapsar la sidebar.
  * **Icono y texto** (`UIButton` con `icon`): los ítems de navegación (con la sidebar colapsada queda el icono y el nombre pasa al tooltip, como ya hace `UIAppShell`), los botones primarios de cada sección («Generar», «Exportar», «Construir») y las confirmaciones destructivas.
  * **Solo texto**: etiquetas de campos, enlaces dentro de un párrafo y opciones de selectores.
  * El nombre accesible de un botón de solo icono es su `aria-label`, y el tooltip muestra el mismo texto. Un conmutador usa `aria-pressed` o cambia su etiqueta, nunca solo el icono.
* **D-5: aplicación** a lo que existe al ejecutar:
  * **Tema**: `UIThemeToggle` con `theme-light`, `theme-dark` o `theme-system` y la etiqueta `theme.change` («Cambiar tema: Claro. Siguiente: Oscuro»). En Ajustes, el selector muestra el icono junto a cada opción.
  * **Nav**: cada entrada de `NAV` gana `icon`, que `UIAppShell` ya muestra.
  * **Cola** (`JobRow`, `QueuePanel`): cancelar, reintentar, abrir carpeta, estrella y asa de arrastre con `UIIconButton`. El estado del trabajo gana un icono junto a su texto: en cola, corriendo (con giro), listo y error.
  * **Paleta** (`UICommandPalette`): el icono de la sección o la acción a la izquierda de cada resultado.
  * **Narración** (006): reproducir, comparar, regenerar, estrella, abrir carpeta e importar guion. «Generar» queda con icono y texto.
  * **Ajustes**: el icono en «Restablecer elecciones», con texto.
* **D-6: catálogo**: las etiquetas de los botones de solo icono van a `messages/{es,en,pt}.json` (`action.play`, `action.open_folder`…) y se definen una vez; varias pantallas reutilizan `action.*`.

## 4. Fuera de alcance

* Iconos propios o un set dibujado para la marca, y el icono de la app de Tauri (es del instalador, 022).
* Componentes base nuevos que ya trae la 008: `UIIcon`, `UIIconButton`, `UITooltip` y la sidebar colapsable.
* Animaciones de iconos más allá del giro del estado «corriendo».
* Rediseñar la disposición de las pantallas: solo cambian los botones e ítems que pasan a icono.

## 5. Criterios de aceptación

* **AC-1**: WHEN se renderiza `UIIcon` con cada nombre de D-2 THEN dibuja un svg con `aria-hidden="true"`, y TypeScript rechaza un nombre que no está en el mapa. Lo verifica: `client/tests/unit/src/shared/components/atoms/UIIcon/index.test.tsx` ampliado (un caso por nombre nuevo).
* **AC-2**: WHEN el tema está en `light`, `dark` o `system` THEN `UIThemeToggle` muestra el icono `theme-light`, `theme-dark` o `theme-system` (sin la palabra visible), su nombre accesible dice el modo actual y el siguiente, y al pulsarlo pasa al siguiente. Lo verifica: el test de `molecules/UIThemeToggle`.
* **AC-3**: WHEN se colapsa la sidebar THEN cada ítem de `NAV` muestra su icono, con el nombre en el tooltip y en `aria-label`. Lo verifica: `tests/e2e/shell/happy-sidebar-collapse.e2e.ts` (de la 008), ampliado con los iconos.
* **AC-4**: WHEN se abren el shell, la cola con un trabajo de cada estado, Ajustes y Narración, en claro y en oscuro THEN axe no reporta fallos serios ni críticos (`button-name` incluido) y cada botón de solo icono tiene un tooltip. Lo verifica: `tests/e2e/shell/happy-apariencia-axe.e2e.ts` ampliado y `tests/e2e/shell/happy-icons-tooltips.e2e.ts`.
* **AC-5**: WHEN se construye el client THEN el budget no crece más de 10 KB gzip respecto del baseline de la 008, y solo llegan al bundle los iconos importados por `UIIcon`. Lo verifica: `python -m devtools test-runner --type=budget`.

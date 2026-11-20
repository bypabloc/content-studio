# Decisiones y lo que se revisa antes de pasar a `main`

Aquí va cada decisión que un agente tomó solo al ejecutar una spec (la opción correcta, no la más rápida) y todo lo que hay que aplicar o revisar **antes** de publicar en `main`: un venv nuevo que instalar, un modelo que descargar, una licencia que confirmar para uso comercial, un paso manual. Cada ficha se borra al aplicarla, en un PR a `dev`, con su fila. Lo que se revisa **después** va en [`../PENDING/`](../PENDING/README.md).

Nombre: `<spec>-<tema>.md` (sin spec, `<tema>.md`). Formato:

```markdown
# <spec>: <decisión en una línea>

- **Contexto**: qué se encontró y por qué hubo que elegir.
- **Elegida**: la opción y su motivo (la correcta, no la más rápida).
- **Descartadas**: cada alternativa y por qué no.
- **Cómo revertir**: commit o pasos para volver atrás.
- **Cómo comprobarla**: comando o prueba que la confirma.
- **Pendiente**: ficha de `../PENDING/` si deja trabajo para después.
```

| Ficha | Qué | Antes de |
| :--- | :--- | :--- |
| [003-baselines](003-baselines.md) | Baselines de tamaño, espejo y cobertura: deuda registrada, no reglas nuevas | `main` |
| [003-hooks-sin-unit](003-hooks-sin-unit.md) | pre-commit y pre-push sin `unit` (recursión con los tests de hooks) | `main` |
| [003-mypy-overrides](003-mypy-overrides.md) | mypy con `ignore_errors` por módulo heredado | `main` |
| [003-cobertura-ci](003-cobertura-ci.md) | Cobertura y espejo medidos en Windows; la CI de Linux aún no corrió | el merge a `dev` |
| [004-candado-gpu](004-candado-gpu.md) | El candado de GPU vive en el server y devtools lo importa | `main` |
| [004-cancelar-procesos](004-cancelar-procesos.md) | Cancelar termina el árbol del proceso: taskkill en Windows, grupo en POSIX | `main` (prueba en WSL) |
| [004-recomendados-narracion-musica](004-recomendados-narracion-musica.md) | La narración recomienda VoxCPM2, no Qwen 0.6B | `main` (narración real, T9) |
| [004-cli-salida-y-token](004-cli-salida-y-token.md) | `studio` rechaza `--output` y `--folder`; `serve` imprime el token que genera | `main` |
| [004-duracion-musica](004-duracion-musica.md) | La música sale en 12 s y no en 15: el recorte de silencio del motor (PENDING 001) | `main` (decisión del usuario) |
| [004-recuperacion-procesos](004-recuperacion-procesos.md) | Al arrancar, el server interrumpe solo los trabajos cuyo proceso murió | `main` (prueba en WSL) |
| [004-cobertura-linux-gpu-lock](004-cobertura-linux-gpu-lock.md) | `gpu_lock.py` queda bajo el 80 % solo en Linux y entra al baseline de cobertura | `main` |
| [005-tanstack-query](005-tanstack-query.md) | Dependencia nueva: TanStack Query guarda los datos del server, y SSE los actualiza | el merge a `dev` |
| [005-typescript-5](005-typescript-5.md) | TypeScript 5.9.3, no 7: `openapi-typescript` necesita su API JavaScript | el merge a `dev` |
| [005-cobertura-client](005-cobertura-client.md) | Cobertura del client al 80 % por archivo, sin shadcn ni `main.tsx` | el merge a `dev` |
| [005-sonner](005-sonner.md) | Dependencia nueva: sonner para los toasts de los trabajos terminados | el merge a `dev` |
| [005-dnd-kit](005-dnd-kit.md) | Dependencia nueva: @dnd-kit para reordenar la cola con teclado y ratón | el merge a `dev` |
| [005-plugins-tauri-js](005-plugins-tauri-js.md) | Plugins JS de opener y notification de Tauri para abrir la carpeta y avisar en Windows | el merge a `dev` |
| [005-select-prefix](005-select-prefix.md) | Las elecciones de los selectores van bajo `select.` y Restablecer solo borra ese prefijo | el merge a `dev` |
| [005-all-sin-e2e](005-all-sin-e2e.md) | `all` incluye budget y deja e2e fuera (Chromium): se aparta de D-9 | el merge a `dev` |
| [005-worktree-prepare](005-worktree-prepare.md) | `prepare` instala con bun y enlaza el target de Cargo; ya no enlaza node_modules | el merge a `dev` |
| [005-teclado-cola](005-teclado-cola.md) | Reordenar con teclado: sensor con coordenadas de fila y anuncios en es.json | el merge a `dev` |
| [005-ci-windows-rust](005-ci-windows-rust.md) | El job `tauri` de CI compila Tauri en Windows y corre también `cargo test` | el merge a `dev` |
| [005-espejo-client-baseline](005-espejo-client-baseline.md) | La auditoría del espejo de client arranca con 8 módulos en el baseline (D-9) | el merge a `dev` |
| [005-jsx-literales](005-jsx-literales.md) | AC-8 se comprueba con `react/jsx-no-literals` de oxlint, como error | el merge a `dev` |
| [005-cors-tauri](005-cors-tauri.md) | La API acepta solo los orígenes de la ventana de Tauri (CORS): sin esto la app no carga datos | el merge a `dev` |
| [005-opener-abrir-carpeta](005-opener-abrir-carpeta.md) | «Abrir carpeta» de los avisos usa `opener:allow-open-path` sin alcance | antes de main (alcance con la 022) |
| [lote-renumeracion-007-021](lote-renumeracion-007-021.md) | Specs renumeradas tres veces de la 007 en adelante (iconos y editor; i18n; componentes); la carpeta del lote conserva `001-017-studio` | la 023 (cierre del lote) |
| [005-desvios-de-diseno](005-desvios-de-diseno.md) | Desvíos de D-1 (sin shadcn), D-2 (CSP amplia), D-4 (theme-init y Geist) y D-8 (confirm nativo) | el merge a `dev` no depende de ellos |
| [006-bun-hoisted-worktree](006-bun-hoisted-worktree.md) | El worktree instala con el enlazador hoisted: el límite de rutas de Windows rompe el enlazador por defecto | el merge a `dev` de la 006 |
| [006-linter-ejemplo-ac1](006-linter-ejemplo-ac1.md) | El ejemplo del AC-1 lleva punto final: sin él, la regla 3 lo marca también | el merge a `dev` |
| [006-linter-criterios](006-linter-criterios.md) | El linter comprueba la regla 3 por párrafo y la 6 por la coma de la enumeración; reusa las marcas de `segments.py` | el merge a `dev` |
| [006-linter-siglas](006-linter-siglas.md) | La regla 2 usa una lista corta de siglas: el repo no tiene diccionario | el merge a `dev` |
| [006-linter-cspell](006-linter-cspell.md) | `script_lint.py` se revisa con español además de inglés en cspell, como el alias del guion | el merge a `dev` |
| [006-media-cache](006-media-cache.md) | La caché de medios va en memoria, no en la tabla `media_cache` de D-3 | el merge a `dev` |
| [006-soundfile-dev](006-soundfile-dev.md) | `soundfile` entra al grupo `dev` del workspace para probar el pipeline sin GPU | el merge a `dev` |
| [006-bloques-en-disco](006-bloques-en-disco.md) | Cada toma guarda `blocks/` y `script.json` en su carpeta, en float de 32 bits | el merge a `dev` |
| [006-narration-sin-torch](006-narration-sin-torch.md) | `narrate()` no importa torch: el pico de VRAM sale de `peak_vram_gib()` y las pruebas la sustituyen | el merge a `dev` |
| [006-migracion-3](006-migracion-3.md) | La migración de `starred` y `group_key` es la 3 del código: la 2 ya es `owner_pid` | el merge a `dev` |
| [006-regenerar-sin-estado](006-regenerar-sin-estado.md) | Regenerar reconstruye los bloques desde `script.json` y copia los que no cambian | el merge a `dev` |
| [006-tomas-y-grupo](006-tomas-y-grupo.md) | Las tomas de un mismo texto comparten `group_key`, que hereda la regeneración | el merge a `dev` |
| [006-dialog-js](006-dialog-js.md) | Dependencia nueva: `@tauri-apps/plugin-dialog` (JS) para «Importar» con el diálogo del sistema | el merge a `dev` |
| [006-editor-capa](006-editor-capa.md) | Los avisos del editor se pintan en una capa detrás del campo, con el texto del server en el tooltip | el merge a `dev` |
| [006-licencia-y-opciones](006-licencia-y-opciones.md) | La licencia se guarda por motor (`license.accepted.<motor>`) y la elección espera a que se guarde | el merge a `dev` |
| [006-masterizacion-cspell](006-masterizacion-cspell.md) | «Masterización» es palabra permitida de cspell en `client/messages/es.json` | el merge a `dev` |
| [006-wavesurfer](006-wavesurfer.md) | Dependencia nueva: `wavesurfer.js` 8.1.0 (exacta) dibuja la onda con los picos del server | el merge a `dev` |
| [006-tomas-desde-la-carpeta](006-tomas-desde-la-carpeta.md) | El resultado lee `script.json` y el `.json` de la toma de su carpeta; no hay endpoint nuevo | el merge a `dev` |
| [006-regenerar-sin-evaluacion](006-regenerar-sin-evaluacion.md) | La toma regenerada no se evalúa con whisper: Comparar la muestra como «Sin evaluar» (AC-3 impide reintentar los bloques ajenos) | antes de main |
| [006-masterizacion-recalcula-ganancia](006-masterizacion-recalcula-ganancia.md) | Regenerar un párrafo recalcula la ganancia de la toma: los bloques ajenos quedan iguales, pero su nivel en el `.wav` final no queda idéntico | antes de main |
| [007-job-id-entero](007-job-id-entero.md) | El id de trabajo en la ruta es entero: `/jobs/nope` da 422 de FastAPI y las pruebas usan `/jobs/999` | el merge a `dev` |
| [007-catalogo-en-el-server](007-catalogo-en-el-server.md) | El catálogo de textos vive en el paquete del server y el client lo importa con `@messages` | antes de main |
| [007-pt-br](007-pt-br.md) | El portugués es pt-BR (Brasil), no pt genérico ni pt-PT | antes de main |
| [007-detector-heuristica](007-detector-heuristica.md) | El detector de textos sueltos usa una heurística, no un análisis de lenguaje | antes de main |
| [007-descripciones-cli](007-descripciones-cli.md) | Las descripciones de motores y modelos del CLI quedan en inglés | antes de main |
| [007-cspell-pt](007-cspell-pt.md) | El diccionario de portugués de cspell es una dependencia de desarrollo de la raíz | antes de main |
| [008-paquete-cn](008-paquete-cn.md) | `cn` se toma del paquete `cn` 0.5.0 de shadcn (MIT), no de un `clsx` + `tailwind-merge` propio | antes de dev |
| [008-base-ui-shadcn](008-base-ui-shadcn.md) | La base de componentes es `@base-ui/react` con shadcn, con las versiones exactas de klinikae | antes de dev |
| [008-shadcn-codigo-de-proveedor](008-shadcn-codigo-de-proveedor.md) | Las primitivas de shadcn quedan fuera de tamaño, ortografía, espejo y cobertura: son código de proveedor | antes de dev |
| [008-clases-tailwind-no-son-texto](008-clases-tailwind-no-son-texto.md) | Una lista de clases de Tailwind no cuenta como texto visible en el detector TS | antes de dev |
| [008-ui-box](008-ui-box.md) | `UIBox` es el contenedor genérico, y solo lo importan moléculas y organismos | antes de dev |
| [008-atomos-adaptados](008-atomos-adaptados.md) | Los átomos de klinikae se adaptan: enlace con hash, set de íconos recortado, pruebas sin jest-dom | antes de dev |
| [008-moleculas-nativas](008-moleculas-nativas.md) | Las moléculas no tienen etiquetas nativas: átomos o roles ARIA | antes de dev |
| [008-moleculas-adaptadas](008-moleculas-adaptadas.md) | Adaptaciones de moléculas: selector recordado, tema controlado y tests por rol | antes de dev |
| [008-organismos-adaptados](008-organismos-adaptados.md) | Organismos sin etiquetas nativas: cierre con `UIButton`, título con rol de encabezado y la barra flotante partida | antes de dev |
| [008-graficas-carga-perezosa](008-graficas-carga-perezosa.md) | Gráficas con `lazy()` y dos átomos nuevos (cruz y hueco) fuera del inventario de D-3 | antes de dev |
| [008-fechas-intl-es](008-fechas-intl-es.md) | `UIDateRangePicker` formatea en `es` fijo, sin el idioma activo | el cierre de la 008 |
| [008-workers-vitest](008-workers-vitest.md) | vitest usa 6 workers: con 23, los selectores `lazy()` no llegan a su espera de 5 s en esta máquina | antes de dev |
| [008-appshell-cola-bajo-secciones](008-appshell-cola-bajo-secciones.md) | La cola va bajo las secciones de la barra, no a la derecha como dice AC-7 (Ronda 5 y «como antes») | antes de dev |
| [008-e2e-narracion-combobox](008-e2e-narracion-combobox.md) | Los e2e de narración esperan el combobox del motor («★ voxcpm2»), no un select nativo; el e2e no está en `all` | antes de dev |
| [008-licensedialog-en-narracion](008-licensedialog-en-narracion.md) | `LicenseDialog` pasa a `features/narration` sobre `UIDialog`; el foco inicial ya no cae en «Aceptar» | antes de dev |
| [008-atomos-nuevos-t6](008-atomos-nuevos-t6.md) | Átomo `UIImage`, `play` y `pause` en `UIIcon`, `role` en vez de `output` y `aside`; el reproductor pasa a 44 px | antes de dev |
| [008-ui-structure-etapa](008-ui-structure-etapa.md) | La etapa `ui-structure` (AST) bloquea etiquetas nativas fuera de átomos; `fieldset` pasa a `role="group"` y `time` a `UITime` | antes de dev |
| [008-jerarquia-oxlint](008-jerarquia-oxlint.md) | La jerarquía D-4 se hace cumplir con overrides de oxlint; el inventario de componentes lo guarda un test (`UIToast` exporta `UIToaster`) | antes de dev |
| [008-excluidos-de-klinikae](008-excluidos-de-klinikae.md) | Los 16 componentes de D-3 que no se copian (clínica, auth, encuestas, usuarios y móvil) | antes de dev |
| [008-tokens-adaptados](008-tokens-adaptados.md) | El tema se adapta: se suman los colores que usan los componentes, no se reemplaza por el de klinikae | antes de dev |
| [008-appshell](008-appshell.md) | `UIAppShell` reemplaza al Shell y a la Sidebar: barra colapsable con `Ctrl+B`; `Sidebar.tsx` y `ThemeToggle.tsx` se borran | antes de dev |
| [008-budget](008-budget.md) | El bundle inicial crece 69,7 kB gzip sobre la 007 (tope de D-9: 90 kB); el límite de `budget` pasa a 228 kB | antes de dev |
| [009-iconos-sustitutos](009-iconos-sustitutos.md) | `stop` y `keyframe` usan `Square` y `Diamond`: lucide 1.58 no tiene `Stop` ni icono de fotograma clave | antes de dev |

Las de la 001 y la 002 se aplicaron y se borraron. Su texto completo sigue en el historial de git (commit `520e911`).

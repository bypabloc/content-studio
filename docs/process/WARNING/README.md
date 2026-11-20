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
| [005-opener-abrir-carpeta](005-opener-abrir-carpeta.md) | «Abrir carpeta» de los avisos usa `opener:allow-open-path` sin alcance | antes de main (alcance con la 015) |
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

Las de la 001 y la 002 se aplicaron y se borraron. Su texto completo sigue en el historial de git (commit `520e911`).

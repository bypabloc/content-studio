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
| [009-iconos-cola-tema](009-iconos-cola-tema.md) | `chevron-up` fuera de D-2 para plegar la cola; iconos de estado; el tema pasa a `UIIconButton` con `theme.change` | antes de dev |
| [009-iconos-narracion-ajustes](009-iconos-narracion-ajustes.md) | Iconos de Narración y Ajustes; la barra colapsable envuelve su trigger en `UITooltip` (shadcn no se edita) | antes de dev |
| [010-perfiles-y-paso-3](010-perfiles-y-paso-3.md) | Perfiles en `reference/<perfil>/`: el paso 3 usa el mapa de renombres del paso 2; los `.txt` versionados se mueven con `git mv` | antes de dev |
| [010-kit-tomas-y-nombres](010-kit-tomas-y-nombres.md) | Las tomas de perfil van en `profile_takes.py` (`takes.py` es de la 006); la subida es el WAV crudo, sin multipart; el texto sale de cada guion | antes de dev |
| [010-chequeo-de-toma](010-chequeo-de-toma.md) | Tolerancias del chequeo (pico, duración, bordes, pausas, ruido y texto); los bordes se miden, no se recortan; sin whisper es aviso, no `retake` | antes de dev |
| [010-import-en-modulo-propio](010-import-en-modulo-propio.md) | La ruta de importar vive en su módulo espejo (`voices_import.py`), no en `voices.py` | antes de dev |
| [010-i18n-t-en-python](010-i18n-t-en-python.md) | El gate i18n cuenta las claves `t('…')` del server; `voice.check.` deja de ser prefijo dinámico | antes de dev |
| [010-consentimiento-en-es](010-consentimiento-en-es.md) | El texto del consentimiento se guarda en español, aunque la UI esté en otro idioma | antes de dev |
| [010-progreso-por-estilo](010-progreso-por-estilo.md) | El progreso del build cuenta cada estilo una vez y cada voz ocupa un tramo del trabajo | antes de dev |
| [010-vumetro-en-ciclo-7](010-vumetro-en-ciclo-7.md) | El vúmetro (LevelMeter) se hace con su pantalla en el ciclo 7; el hook ya entrega los niveles | antes de dev |
| [010-worklet-y-permiso](010-worklet-y-permiso.md) | El worklet se carga con `?worker&url`; el permiso del micrófono se decide probado en la app | antes de dev |
| [010-fixture-wav-compartida](010-fixture-wav-compartida.md) | Fixture de WAV compartida entre client y server, con su generador | antes de dev |
| [010-progreso-sobre-el-kit](010-progreso-sobre-el-kit.md) | El progreso de un perfil cuenta los 12 estilos obligatorios del kit y se oculta hasta que llega | antes de dev |
| [010-cliente-patch-upload-y-borrado](010-cliente-patch-upload-y-borrado.md) | El cliente de la API suma PATCH y la subida de un cuerpo crudo; borrar siempre pide la papelera | antes de dev |
| [010-presupuesto-del-cliente](010-presupuesto-del-cliente.md) | El presupuesto del JS inicial sube de 228 a 232 kB por la pantalla de Mis voces; la importación diferida no baja la cifra con el medidor actual | antes de dev |
| [010-remuestreo-al-subir](010-remuestreo-al-subir.md) | La toma de un micrófono que no da 48 kHz se convierte a 48 kHz al subirla, y el chequeo lo anota | antes de dev |
| [010-wav-extensible-en-tomas](010-wav-extensible-en-tomas.md) | ffmpeg escribe las tomas de 24 bits como WAV extensible; las pruebas las leen con soundfile | antes de dev |
| [010-medidor-como-atomo](010-medidor-como-atomo.md) | El medidor de nivel es el átomo `UILevelMeter`, no un `LevelMeter` de la pantalla (sustituye a 010-vumetro-en-ciclo-7) | antes de dev |
| [010-grabar-desde-la-ficha](010-grabar-desde-la-ficha.md) | «Grabar» abre el asistente en lugar de la ficha; «Volver a la ficha» se bloquea durante una toma | antes de dev |
| [010-espacio-y-fase-en-ref](010-espacio-y-fase-en-ref.md) | La barra espaciadora lee la fase desde una referencia, para no repetir la grabación al pulsar rápido | antes de dev |
| [010-prueba-sala-sin-micro](010-prueba-sala-sin-micro.md) | Si el micrófono no abre, la prueba de sala avisa y cancela su temporizador | antes de dev |
| [010-negrita-del-guion](010-negrita-del-guion.md) | El teleprompter pinta en negrita el énfasis `**palabra**` del guion | antes de dev |
| [010-subida-acepta-vista-de-bytes](010-subida-acepta-vista-de-bytes.md) | `upload` del cliente acepta una vista de bytes (TypeScript 5.9 tipa `Uint8Array` con su buffer) | antes de dev |
| [010-repetir-es-otra-toma](010-repetir-es-otra-toma.md) | «Repetir» graba otra toma del mismo estilo, igual que «Grabar»; las tomas no se sobrescriben | antes de dev |
| [010-medir-arranque-en-budget](010-medir-arranque-en-budget.md) | La etapa `budget` mide solo el JS de arranque (entrada y `modulepreload`); el límite sigue en 232 kB | antes de dev |
| [010-enfasis-atomo](010-enfasis-atomo.md) | El énfasis del guion es el átomo `UIEmphasis`: el `strong` nativo no va fuera de los átomos | antes de dev |
| [010-importar-tramo-sin-region](010-importar-tramo-sin-region.md) | Superada: el tramo se marca sobre la onda del origen ([010-region-sobre-la-onda](010-region-sobre-la-onda.md)) | antes de dev |
| [010-favorita-primera-y-por-defecto](010-favorita-primera-y-por-defecto.md) | El selector de voz pone la favorita primero y la usa por defecto (AC-9) | antes de dev |
| [010-ac10-sin-texto-de-ui](010-ac10-sin-texto-de-ui.md) | AC-10 busca rutas y dependencias del grabador, no la palabra «grabar» de la UI | antes de dev |
| [010-e2e-voces-sinteticas](010-e2e-voces-sinteticas.md) | Las respuestas e2e de Mis voces son sintéticas; el harness deja pasar cuerpos binarios | antes de dev |
| [010-region-sobre-la-onda](010-region-sobre-la-onda.md) | El tramo de importar se marca sobre la onda del origen (D-4), con endpoint de picos y gate propio | antes de `main` |
| [010-construir-sobre-voces-del-usuario](010-construir-sobre-voces-del-usuario.md) | El AC-7 real construiría sobre voces del usuario (junctions al principal): se pide decisión | antes de `main` |
| [010-revision-visual-capturas](010-revision-visual-capturas.md) | Revisión visual de las capturas: 14 notas; la alineación se corrigió y el resto queda en PENDING | antes de `main` |
| [010-consola-cp1252-en-build](010-consola-cp1252-en-build.md) | La entrada de voces pone la consola en errors=replace: un ← reventaba en Windows (cp1252) | antes de `main` |
| [010-captura-pcm](010-captura-pcm.md) | Captura PCM sin procesado para las tomas (AC-3): 48 kHz, mono, 24 bits; el server convierte si hace falta | antes de `main` |
| [010-permiso-microfono-webview2](010-permiso-microfono-webview2.md) | El micrófono entra sin diálogo: `on_permission_request` concede solo el micrófono en WebView2; el usuario lo probó en la app | antes de `main` |
| [010-borrar-toma](010-borrar-toma.md) | Borrar una toma la manda a la papelera del perfil con su chequeo; la referencia elegida no cambia | antes de `main` |
| [010-microfono-en-ajustes](010-microfono-en-ajustes.md) | El micrófono se elige en Ajustes (`select.recording.microphone`), con `exact`; la lista sale al pulsar «Ver micrófonos» | antes de `main` |
| [010-micro-en-uso-y-registro](010-micro-en-uso-y-registro.md) | Indicador «Micrófono en uso» en la grabación y registro en `logs/recording/`, apagado por defecto (`diagnostics.recording_log`) | antes de `main` |
| [011-categorias](011-categorias.md) | Categoría de los 126 presets y catálogo `GET /music/styles` | `main` |
| [011-duracion-exacta](011-duracion-exacta.md) | Duración exacta en música: plan, margen, recorte y fade | `main` |
| [011-muestras](011-muestras.md) | Muestras de 10 s por preset con semilla fija; `studio music samples` y `--model` | `main` |
| [011-db-despues-del-subcomando](011-db-despues-del-subcomando.md) | `--db` también después del subcomando (cierra PENDING 004) | `main` |
| [011-comparar-musica](011-comparar-musica.md) | Comparar y elegir pistas con `tracks.json` (sin generalizar CompareTakes) | `main` |
| [012-rutas-externas](012-rutas-externas.md) | Prioridad de los motores administrados y respaldo a los externos en desarrollo | `main` |
| [012-mover-entre-discos](012-mover-entre-discos.md) | Copia verificada, turno exclusivo de traslado y enlaces históricos de salidas | `main` |
| [012-winget](012-winget.md) | Detectar las herramientas y actualizar el PATH del proceso tras la instalación | `main` |
| [012-recetas](012-recetas.md) | Versiones de paquetes, commits y revisiones de pesos fijados a partir de la instalación de Windows | `main` |
| [012-desinstalacion-externa](012-desinstalacion-externa.md) | `force` elimina solo el venv externo conocido y conserva cachés y datos ajenos | `main` |
| [012-error-disk-full](012-error-disk-full.md) | `disk_full` se localiza como error asíncrono del trabajo | `main` |
| [012-verificacion-voz](012-verificacion-voz.md) | La prueba TTS usa la voz de catálogo `yesid` con consentimiento porque falta `reference/test/` | Al cerrar la 012 |
| [012-pantallas-almacenamiento](012-pantallas-almacenamiento.md) | Umbrales de VRAM y métricas de disco sin seguir enlaces | Al cerrar la 012 |
| [012-aceptacion-sin-usuario](012-aceptacion-sin-usuario.md) | La bienvenida se prueba con e2e; la revisión visual y las capturas quedan en PENDING y no bloquean | `main` (revisión visual en PENDING) |
| [012-trabajos-engine-uninstall-en-error](012-trabajos-engine-uninstall-en-error.md) | Tres trabajos `engine.uninstall` fallidos se conservan como historial, sin reintentar | `main` |
| [lote-limpieza-huerfanos](lote-limpieza-huerfanos.md) | Se borraron 41 de 49 carpetas huérfanas de `content-studio-worktrees/`; 8 bloqueadas en PENDING | No bloquea |
| [013-plan-y-render](013-plan-y-render.md) | Sin palabras no hay cortes; remap pega los tiempos del corte al borde; crossfade de 15 ms y grafo en archivo | `main` |
| [013-render-precision](013-render-precision.md) | Tasa de cuadros de la fuente con `-r` (sin ella, 25 fps); yuv420p; NVENC p5 cq19 o libx264 crf 18 | `main` |
| [013-transcripcion-cache](013-transcripcion-cache.md) | Migración 4 (la 3 es de la 006); familia `transcription`; caché por sha1 y modelos del catálogo | `main` |

Las de la 001 y la 002 se aplicaron y se borraron. Su texto completo sigue en el historial de git (commit `520e911`).

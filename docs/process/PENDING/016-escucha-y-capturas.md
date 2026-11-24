# 016: escucha del usuario, capturas, medición del ducking y corrida de la UI

**Qué falta.**

- **Escucha.** Ningún valor por defecto (-12 dB, 300 ms, -6 dB) se ha escuchado todavía. El gusto lo decide el usuario (`verify-before-claiming-done.md`). Rutas para escuchar: `out/mix/2026-11-22-7-mix-render/mix.wav` (transcript), `…-8-…/mix.wav` (sidechain), `…-9-…/mix.mp4` (video `replace`) y `…-10-…/mix.mp4` (video `under`).
- **Ducking medido en la mezcla real.** Los espectrogramas no lo muestran (`image-reader`). Para medirlo hace falta el nivel de la música dentro y fuera de los tramos de voz: renderizar la misma mezcla sin voz, o medir la envolvente del `duck.cmd`. El test sintético de AC-3 pasa; la medición real queda pendiente.
- **Capturas en claro y en oscuro** de la sección Mezcla. No se han hecho con la app: la corrida de la UI no se ha ejecutado.
- **Corrida desde la UI real.** Los pasos 1 y 2 de `03-verificacion-final.md` (Narración → «Mandar a Mezclar», Mezcla → «Generar música», mover y borrar regiones en la línea de tiempo, vista previa) no se han hecho con la app de escritorio. Las mezclas reales salieron por el CLI con los mismos servicios.
- **Tests e2e de la UI** (ya en el repo, sin correr contra la app real): `tests/e2e/mix/happy-send-and-generate.e2e.ts`, `happy-edit-ramps-render.e2e.ts`, `happy-video-under.e2e.ts` y `neg-music-too-short.e2e.ts`.

**Cómo cerrarlo.** Abrir la app (`bun run --cwd client tauri dev`), seguir el flujo de `03-verificacion-final.md` y guardar las capturas en `tmp/spec-016/`.

**Dónde.** `docs/specs/001-017-studio/016-mix-ducking/03-verificacion-final.md`, secciones 2 y 3 (la carpeta la borró la 023: está en el historial de git, `git log --all -- docs/specs/001-017-studio/016-mix-ducking`).

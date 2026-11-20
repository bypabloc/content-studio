# 010: el WAV de `encodeWav` se verifica por huella, sin versionar audio

- **Contexto**: AC-3 pide que ffprobe lea el WAV que escribe el client. La guarda de staging rechaza audio en el repo (`git-workflow.md`), así que la fixture de 144 KB no se puede versionar.
- **Elegida**: `client/scripts/wav-fixture.ts` fija el SHA-256 de los bytes que escribe `encodeWav` para una senoidal de 1 s, en `server/tests/fixtures/voices/client-sine-1s-48k-24b.sha256` (texto). El client comprueba esa huella. El server reconstruye el mismo WAV en Python (float32 y redondeo de `Math.round`), comprueba que su huella coincide y se lo pasa a ffprobe. Vitest corre desde `client/`, así que la ruta sale de `process.cwd()`: en jsdom, `import.meta.url` no es una URL de archivo.
- **Descartadas**: versionar el WAV (la guarda lo prohíbe, y cambiarla es decisión del usuario); codificarlo en base64 (esquiva la guarda, así que no); generar el WAV en cada prueba sin unir los dos lados.
- **Cómo revertir**: quitar el `.sha256`, el script y las dos pruebas que lo usan, en un commit.
- **Cómo comprobarla**: `cd client && bun scripts/wav-fixture.ts` no cambia el `.sha256` (`git status` limpio); `uv run pytest server/tests/unit/src/content_studio/common/test_ffmpeg.py` (incluye la comprobación de la huella y ffprobe).
- **Pendiente**: el remuestreo a 48 kHz, en PENDING `010-remuestreo-48-khz.md`.

---
modulo: music
actualizada: 2026-11-24
---

# Música

## Qué resuelve

Música de fondo instrumental para videos, en local, sin voz ni letra.

## Qué hace hoy

- `uv run studio music --model <m> --style <e…> --duration <s>`: una pista por estilo, cada una en `out/music/<AAAA-MM-DD>-<id>-<slug>/` con `params.json`. El comando encola el trabajo y lo corre en su proceso; `studio serve` corre los de la cola.
- 126 estilos con tonalidad, BPM y compás definidos; el texto libre exige `--key` y `--bpm`.
- Motores: ACE-Step 1.5 (recomendado, ~30 s por pista) y HeartMuLa (~5 min por pista), cada uno en su venv.
- Duración exacta: la pista sale con los segundos pedidos (±10 ms); si queda corta, regenera hasta 2 veces y avisa `music_short`.
- `studio music samples`: una muestra de 10 s por preset para el buscador. Cada trabajo deja `tracks.json` con sus pistas.
- Sección Música en la app: motor, duración con «Igualar a…», buscador de estilos (categoría, modo, BPM, favoritos) o texto libre, «Avanzado» con variantes, y comparar con «Elegir».
- Las pistas se mezclan con la voz (ducking, LUFS final, video opcional) en la sección Mezcla: ver [mix.md](mix.md).

## Dónde vive

- Código: `server/src/content_studio/music/` (estilos en `styles.py`, motores en `engines/` con `registry.py`). El trabajo que encola `studio` está en `server/src/content_studio/services/music.py`.
- Datos: `server/data/music/` (README, investigación, venvs, modelos). Uso y rendimiento: [server/data/music/README.md](../../../server/data/music/README.md).

## Versiones de los motores (spec 026, 2026-11-25)

| Motor | Python | Salida de 30 s (verificada) | Nota |
| :--- | :---: | :--- | :--- |
| acestep | 3.12 | 30,0 s, -14,4 LUFS integrado, volumen medio -15,6 dB, pico -0,5 dBFS, sin voz (demucs -42,4 dB) | Su pyproject exige Python menor que 3.13 y torch 2.7.1 |
| heartmula | 3.13 | 30,0 s, -11,8 LUFS, pico -1,2 dBFS con la revisión anterior; **con voz** (demucs -1,3 dB) | No cumple «siempre instrumental»: ficha WARNING `026-heartmula-voz` |

Fichas: `docs/process/WARNING/026-acestep-version.md`, `026-heartmula-version.md`, `026-heartmula-voz.md`.

## Historial

- 2026-11-24: «Describir en español» sugiere caption, tonalidad, BPM y compás para el texto libre (spec 021).
- 2026-11-18: ficha inicial al adoptar `docs/process/`.
- 2026-11-19: CLI `studio` (004): `python cli.py music` pasa a `uv run studio music`; la salida va a `out/music/<fecha>-<id>-<slug>/`.
- 2026-11-20: spec 011 (música completa): duración exacta, categorías, reintentos, muestras de 10 s, sección Música y comparación de pistas.

## Verificación (2026-11-20)

- Corrida real (ACE-Step, `lofi-chill` y `corporate-minimal`, 2 variantes, 30 s, `--evaluate --retries 1`): 4 pistas de 30,000 s, sin aviso `music_short`, volumen de −13,6 a −14,7 LUFS y pico real de −1,0 dBFS. Sin silencios de 0,3 s o más.
- Espectrograma (revisión visual y `astats`): en `corporate-minimal` v2 la energía por encima de 6 kHz cae unos 25 dB desde ~19,5 s. Queda como pendiente de escucha en `docs/process/PENDING/011-caida-agudos-corporate.md`.
- Pruebas: servidor 830 en verde; client con sus 8 etapas en verde; e2e 27/27 en desktop-chromium (cuatro de Música).
- Muestras de los 126 presets: pendientes (`docs/process/PENDING/011-generar-muestras.md`).


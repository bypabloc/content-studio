---
modulo: music
actualizada: 2026-11-20
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

## Dónde vive

- Código: `server/src/content_studio/music/` (estilos en `styles.py`, motores en `engines/` con `registry.py`). El trabajo que encola `studio` está en `server/src/content_studio/services/music.py`.
- Datos: `server/data/music/` (README, investigación, venvs, modelos). Uso y rendimiento: [server/data/music/README.md](../../../server/data/music/README.md).

## Historial

- 2026-11-18: ficha inicial al adoptar `docs/process/`.
- 2026-11-19: CLI `studio` (004): `python cli.py music` pasa a `uv run studio music`; la salida va a `out/music/<fecha>-<id>-<slug>/`.
- 2026-11-20: spec 011 (música completa): duración exacta, categorías, reintentos, muestras de 10 s, sección Música y comparación de pistas.

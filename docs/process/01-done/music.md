---
modulo: music
actualizada: 2026-11-18
---

# Música

## Qué resuelve

Música de fondo instrumental para videos, en local, sin voz ni letra.

## Qué hace hoy

- `python cli.py music --model <m> --style <e…> --duration <s>`: una pista por estilo en `out/music/`.
- 126 estilos con tonalidad, BPM y compás definidos; el texto libre exige `--key` y `--bpm`.
- Motores: ACE-Step 1.5 (recomendado, ~30 s por pista) y HeartMuLa (~5 min por pista), cada uno en su venv.

## Dónde vive

- Código: `server/src/content_studio/music/` (estilos en `styles.py`, motores en `engines/` con `registry.py`).
- Datos: `server/data/music/` (README, investigación, venvs, modelos). Uso y rendimiento: [server/data/music/README.md](../../../server/data/music/README.md).

## Historial

- 2026-11-18: ficha inicial al adoptar `docs/process/`.

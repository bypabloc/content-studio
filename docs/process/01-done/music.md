---
modulo: music
actualizada: 2026-11-18
---

# Música

## Qué resuelve

Música de fondo instrumental para videos, en local, sin voz ni letra.

## Qué hace hoy

- `python cli.py music --modelo <m> --estilo <e…> --duracion <s>`: una pista por estilo en `out/music/`.
- 126 estilos con tonalidad, BPM y compás definidos; el texto libre exige `--tono` y `--bpm`.
- Motores: ACE-Step 1.5 (recomendado, ~30 s por pista) y HeartMuLa (~5 min por pista), cada uno en su venv.

## Dónde vive

- Código: `src/content_studio/music/` (estilos en `estilos.py`, motores en `motores/` con `registro.py`).
- Datos: `music/` (README, investigación, venvs, modelos). Uso y rendimiento: [music/README.md](../../../music/README.md).

## Historial

- 2026-11-18: ficha inicial al adoptar `docs/process/`.

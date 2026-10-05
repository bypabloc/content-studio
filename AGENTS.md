# social-videos

Audio local para videos, en una RTX 4060 Laptop (8 GB) con WSL2. Hay dos herramientas independientes, cada una con su script, sus venvs y sus modelos dentro de su carpeta:

| Carpeta | Qué genera | Script | Documentación |
| :--- | :--- | :--- | :--- |
| `narration/` | Narración TTS en español neutro clonando una voz (Qwen3-TTS, Chatterbox) | `narration/tts.py` | [narration/README.md](narration/README.md) · [formato del guion](narration/docs/formato-guion.md) · [grabar voces](narration/docs/guiones/README.md) |
| `music/` | Música de fondo instrumental (ACE-Step 1.5, HeartMuLa) | `music/musica.py` | [music/README.md](music/README.md) · [INVESTIGACION.md](music/INVESTIGACION.md) |

**Antes de usar cualquiera de las dos, lee su README**: ahí están el uso, los flags, el rendimiento medido, los tips y los problemas conocidos.

## Atajos

```bash
# Narración (sin grabaciones propias todavía: usar la referencia de prueba)
python narration/tts.py --modelo qwen-0.6b --estilo experta \
  --ref narration/voz/prueba/experta.wav --texto "..."            # → out/narration/

# Música (presets con tonalidad/BPM/compás definidos; texto libre exige --tono y --bpm)
python music/musica.py --modelo acestep --estilo lofi-chill corporate --duracion 30   # → out/music/
```

Los scripts se relanzan solos en su venv, así que se pueden ejecutar con cualquier `python`.

## Reglas

1. **Salidas** en `out/narration/` y `out/music/`, o donde indiquen `--salida` (narration) y `--carpeta` (music). **Logs** en `logs/<herramienta>-<descripción>.log`. Las dos carpetas están gitignoreadas y no se limpian. Las corridas largas (HeartMuLa tarda ~5 min por pista) se lanzan en segundo plano, con la salida en `logs/`.
2. **Un modelo a la vez en la GPU.** Narración y música juntas no caben en 8 GB. Si la VRAM se desborda a la RAM compartida de WSL, todo va ~4× más lento.
3. **La música es siempre instrumental**: nada de voz ni de letra.
4. **Verificar antes de decir "listo"**: correr el script real y revisar la duración, el volumen y el espectrograma (ver los README). El gusto lo decide el usuario: entrégale las rutas.
5. **Licencias**: Qwen3-TTS (Apache 2.0), Chatterbox (MIT), ACE-Step (MIT) y HeartMuLa (Apache 2.0) permiten uso comercial. Clona solo voces con permiso de su dueño.
6. Idioma de trabajo: español, en respuestas concisas y sin adulación. Narración en español neutro latinoamericano, salvo que se pida otro idioma.
7. Los archivos se crean y editan con las herramientas de edición del agente. Bash se usa solo para ejecutar los scripts y ffmpeg. Muestra los resultados con rutas clicables a `out/`.

## Requisitos

`ffmpeg`, `uv` y GPU NVIDIA. La instalación de cada herramienta está en su README.

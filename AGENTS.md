# content-studio

Audio local para videos, en una RTX 4060 Laptop (8 GB) con WSL2. Hay dos herramientas independientes. El código de las dos vive en `src/content_studio/`; sus carpetas (`narration/`, `music/`) guardan solo datos: docs, voces, catálogo, venvs y modelos.

| Carpeta | Qué genera | Código | Documentación |
| :--- | :--- | :--- | :--- |
| `narration/` | Narración TTS en español neutro clonando una voz (Qwen3-TTS, Chatterbox) | `src/content_studio/narration/` | [narration/README.md](narration/README.md) · [formato del guion](narration/docs/formato-guion.md) · [grabar voces](narration/docs/guiones/README.md) |
| `music/` | Música de fondo instrumental (ACE-Step 1.5, HeartMuLa) | `src/content_studio/music/` | [music/README.md](music/README.md) · [INVESTIGACION.md](music/INVESTIGACION.md) |

**Antes de usar cualquiera de las dos, lee su README**: ahí están el uso, los flags, el rendimiento medido, los tips y los problemas conocidos.

## Atajos

Todo se lanza desde `cli.py`, hecho con [Typer](https://typer.tiangolo.com), [Rich](https://rich.readthedocs.io) y [questionary](https://questionary.readthedocs.io): `python cli.py <herramienta> <comando> [flags]`.

- **Sin argumentos** abre un menú con flechas que muestra la VRAM libre y cuántas voces de referencia hay grabadas.
- **Si falta un flag obligatorio o uno es inválido**, el asistente lo pide: listas con descripción (licencia, VRAM y si está instalado cada motor), casillas con filtro para los 126 estilos de música, rutas con Tab y números validados. Después muestra un resumen editable, con los valores por defecto en gris y el comando equivalente, para ejecutar, cambiar o agregar cualquier flag.
- **Con todos los flags**, se ejecuta directo. **Sin TTY** (agentes, scripts, `| cat`), no pregunta nada y se comporta como el script.

```bash
python cli.py                            # menú
python cli.py narration tts              # asistente
python cli.py narration tts --help       # ayuda en tabla: flags, valores, defecto y obligatorios

# Narración (sin grabaciones propias todavía: una voz libre del catálogo con consentimiento)
python cli.py narration tts --modelo qwen-0.6b --estilo experta \
  --voz yesid --texto "..."                                       # → out/narration/

# Grabar las voces de referencia
python cli.py narration grabar --listar

# Voces libres (CC0 o dominio público), aprobadas en los 12 estilos: construir y narrar con una
python cli.py narration voces --construir todas
python cli.py narration tts --modelo cosyvoice3 --voz yesid --texto "..."

# Música (presets con tonalidad/BPM/compás definidos; texto libre exige --tono y --bpm)
python cli.py music --modelo acestep --estilo lofi-chill corporate --duracion 30   # → out/music/
```

`cli.py` funciona con cualquier `python`: si no tiene las dependencias, se relanza con `uv run --script` (están en su cabecera PEP 723). Cada comando, a su vez, se relanza solo en el venv de su motor. También se puede llamar un módulo directo: `PYTHONPATH=src python -m content_studio.narration.tts ...` (o `content_studio.music.musica`, `content_studio.narration.voces.main`), y `uv run content-studio` es lo mismo que `python cli.py`. `grabar` necesita rich y questionary: directo, con `uv run python -m content_studio.narration.grabar.main`.

## Arquitectura

```
cli.py                        shim: relanza con uv si faltan typer/rich/questionary y llama a content_studio.cli.app
src/content_studio/
├── rutas.py                  RAIZ, OUT, LOGS, NARRATION, MUSIC, VOZ, VOCES…
├── comun/                    proceso (relanzar en un venv), ffmpeg, archivos
├── cli/                      Typer: app, menu, flujo (asistente), widgets, args; comandos/ con Comando y REGISTRO
├── narration/                parser (liviano), tts (main), estilos, bloques, pipeline, audio, guion, metadatos, referencia
│   ├── motores/              EspecMotor + MotorTTS (Factory Method) y registro.py con MOTORES
│   ├── texto/ evaluacion/    segmentos y traducción por motor; comparar y revisar (whisper)
│   ├── voces/                catálogo de voces libres: catalogo, fuentes, construir, main
│   └── grabar/               grabar referencias: kit, dispositivos, interfaz, toma, main
└── music/                    parser (liviano), musica (main), estilos, evaluacion
    └── motores/              EspecMusica + MotorMusica y registro.py con MODELOS
```

Dos capas: los `parser.py`, los catálogos y el CLI solo importan stdlib (y typer/rich/questionary en `cli/` y `grabar/`), así `--help` y el asistente funcionan sin los venvs. torch, numpy y las librerías de cada motor se importan dentro de las funciones, ya en el venv del motor.

- **Agregar un motor TTS o de música**: un archivo en `motores/` con su subclase de `MotorTTS` o `MotorMusica`, una entrada `EspecMotor`/`EspecMusica` en `motores/registro.py` (venv, módulo, clase, licencia) y su venv. El parser y el asistente lo toman del registro; en `tests/test_venvs.py` se agrega la librería que importa (`LIBRERIAS`).
- **Agregar un comando del CLI**: una subclase de `Comando` en `cli/comandos/` (clave, módulo, parser liviano con `construir_parser()`) y una línea en `REGISTRO` (`cli/comandos/__init__.py`).
- **Máximo 300 líneas por `.py`** (lo comprueba `tests/test_estructura.py`) y Python 3.10 como mínimo. Detalle en [.claude/rules/codigo-python.md](.claude/rules/codigo-python.md).

## Pruebas

```bash
uv run ruff check && uv run ruff format --check
uv run pytest            # doctests, caracterización, estructura, CLI y bugs (sin GPU; lo mismo corre en CI)
uv run pytest -m local   # además, cada venv de motor importa su librería (solo en este equipo)
```

## Reglas

1. **Salidas** en `out/narration/` y `out/music/`, o donde indiquen `--salida` (narration) y `--carpeta` (music). **Logs** en `logs/<herramienta>-<descripción>.log`. Las dos carpetas están gitignoreadas y no se limpian. Las corridas largas (HeartMuLa tarda ~5 min por pista) se lanzan en segundo plano, con la salida en `logs/`.
2. **Un modelo a la vez en la GPU.** Narración y música juntas no caben en 8 GB. Si la VRAM se desborda a la RAM compartida de WSL, todo va ~4× más lento.
3. **La música es siempre instrumental**: nada de voz ni de letra.
4. **Verificar antes de decir "listo"**: correr el script real y revisar la duración, el volumen y el espectrograma (ver los README). El gusto lo decide el usuario: entrégale las rutas.
5. **Licencias**: VoxCPM2, Qwen3-TTS y HeartMuLa (Apache 2.0), y Chatterbox y ACE-Step (MIT) permiten uso comercial. CosyVoice 3 es Apache 2.0, pero su tarjeta dice "academic purposes": revísalo antes de un uso comercial. OmniVoice (CC-BY-NC) e IndexTTS (bilibili Model Use License) **no** son comerciales. La lista vigente está en `src/content_studio/narration/motores/registro.py`. Clona solo voces con permiso de su dueño.
6. Idioma de trabajo: español, en respuestas concisas y sin adulación. Narración en español neutro latinoamericano, salvo que se pida otro idioma.
7. Los archivos se crean y editan con las herramientas de edición del agente. Bash se usa solo para ejecutar los scripts y ffmpeg. Muestra los resultados con rutas clicables a `out/`.

## Requisitos

`ffmpeg`, `uv` y GPU NVIDIA. La instalación de cada herramienta está en su README.

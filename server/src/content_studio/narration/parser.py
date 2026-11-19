r"""TTS local con clonación de voz: Qwen3-TTS, Chatterbox V3, OmniVoice, VoxCPM2, IndexTTS 2.5 y CosyVoice 3.

Uso (ver narration/README.md):
    python cli.py narration tts --modelo qwen-0.6b --estilo amistosa \
        --texto "Hola, bienvenidos al canal."
    python cli.py narration tts --modelo chatterbox --ref narration/voz/clara.wav \
        --estilo clara --archivo guion.txt --salida out/narration/guion.wav
    python cli.py narration tts --modelo qwen-0.6b --archivo guiones/*.json --salida out/narration/lote
    python cli.py narration tts --modelo omnivoice --archivo guion.txt --semilla 7 --evaluar

--ref acepta un .wav o una carpeta con <estilo>.wav (por defecto narration/voz). --voz usa una voz libre
del catálogo (python cli.py narration voces), solo si está aprobada en todos los estilos.
La transcripción va al lado con el mismo nombre y extensión .txt.
Cada motor corre en su propio venv (ver motores/registro.py). Cada toma deja un .json con sus metadatos.

Pausas en el texto: una línea en blanco agrega 0.6 s; [pausa 1.5] agrega 1.5 s.
Estilo y emoción por párrafo: [estilo: dramatica], [emocion: triste 0.4]. Gestos: [risa], [suspiro],
[respiro]; énfasis: [enfasis]palabra[/enfasis]. Cada motor recibe su traducción (ver texto/traducir.py).
Otras marcas ([breath], <break>, **) se leen en voz alta. Ver narration/docs/formato-guion.md.
Un .json trae "texto" (lista de párrafos), "estilo" e "id" (nombre de la salida).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from content_studio import rutas
from content_studio.narration.estilos import ESTILOS
from content_studio.narration.motores.registro import MOTORES
from content_studio.narration.voces.catalogo import aprobadas

__all__ = ['ESTILOS', 'MOTORES', 'aprobadas', 'construir_parser']  # el CLI lee los catálogos de aquí


def construir_parser() -> argparse.ArgumentParser:
    """Flags del script. cli.py lo usa para preguntar los que faltan y mostrar la ayuda."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        '--modelo', choices=MOTORES, default='voxcpm2', help='motor TTS (por defecto voxcpm2; ver narration/README.md)'
    )
    ap.add_argument('--ref', type=Path, default=rutas.VOZ, help='carpeta de referencias o un .wav concreto')
    ap.add_argument(
        '--voz',
        choices=list(aprobadas(ESTILOS)),
        help='voz libre del catálogo, aprobada en todos los estilos (cli.py narration voces); reemplaza --ref',
    )
    ap.add_argument('--estilo', choices=ESTILOS, help='por defecto el "estilo" del JSON, o experta')
    fuente = ap.add_mutually_exclusive_group(required=True)
    fuente.add_argument('--texto', help='texto a narrar, entre comillas')
    fuente.add_argument('--archivo', type=Path, nargs='+', help='uno o varios .txt o .json; el modelo se carga una vez')
    ap.add_argument(
        '--salida',
        type=Path,
        help='con un solo guion, el .wav; con varios, la carpeta. Por defecto out/narration/',
    )
    ap.add_argument('--lote', type=int, help='frases por pasada en Qwen; por defecto según la VRAM libre')
    ap.add_argument('--semilla', type=int, help='semilla base; por defecto aleatoria. Se imprime y queda en el .json')
    ap.add_argument(
        '--master',
        choices=['voz', 'no'],
        default='voz',
        help='voz: loudness de --lufs con pasa-altos de 70 Hz, sin compresión salvo que el pico lo impida; '
        'no: sin procesar',
    )
    ap.add_argument('--lufs', type=float, default=-16.0, help='loudness objetivo de --master voz (por defecto -16)')
    ap.add_argument(
        '--idioma',
        choices=['es', 'en'],
        default='es',
        help='idioma del motor y de whisper; con en, el estilo por defecto es neutral-en',
    )
    ap.add_argument(
        '--evaluar',
        action='store_true',
        help='al final transcribe cada salida con whisper y la compara, párrafo por párrafo, con el texto pedido',
    )
    ap.add_argument(
        '--reintentos',
        type=int,
        default=0,
        help='con --evaluar: rondas en las que se regeneran solo los párrafos con observaciones',
    )
    return ap

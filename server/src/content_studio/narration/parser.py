r"""TTS local con clonación de voz: Qwen3-TTS, Chatterbox V3, OmniVoice, VoxCPM2, IndexTTS 2.5 y CosyVoice 3.

Uso (ver server/data/narration/README.md):
    studio narration tts --model qwen-0.6b --style friendly --text "Hola, bienvenidos al canal."
    studio narration tts --model chatterbox --ref server/data/narration/reference/clara.wav \
        --style clear --file guion.txt
    studio narration tts --model qwen-0.6b --style expert --file guiones/*.json
    studio narration tts --model omnivoice --style expert --file guion.txt --seed 7 --evaluate

Con `studio` cada trabajo sale en out/narration/<fecha>-<id>-<slug>/ (no se usa --output).
--ref acepta un .wav o una carpeta con <estilo>.wav (por defecto server/data/narration/reference). --voice usa una voz
libre del catálogo (studio narration voices), solo si está aprobada en todos los estilos.
La transcripción va al lado con el mismo nombre y extensión .txt.
Cada motor corre en su propio venv (ver engines/registry.py). Cada toma deja un .json con sus metadatos.

Pausas en el texto: una línea en blanco agrega 0.6 s; [pausa 1.5] agrega 1.5 s.
Estilo y emoción por párrafo: [estilo: dramatica], [emocion: triste 0.4]. Gestos: [risa], [suspiro],
[respiro]; énfasis: [enfasis]palabra[/enfasis]. Cada motor recibe su traducción (ver texto/traducir.py).
Otras marcas ([breath], <break>, **) se leen en voz alta. Ver server/data/narration/docs/formato-guion.md.
Un .json trae "texto" (lista de párrafos), "estilo" e "id" (nombre de la salida).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from content_studio import paths
from content_studio.narration.engines.registry import ENGINES
from content_studio.narration.styles import STYLES
from content_studio.narration.voices.catalog import approved_voices

SUMMARY = 'Local TTS with voice cloning: Qwen3-TTS, Chatterbox V3, OmniVoice, VoxCPM2, IndexTTS 2.5 and CosyVoice 3.'

__all__ = ['STYLES', 'ENGINES', 'approved_voices', 'build_parser']  # el CLI lee los catálogos de aquí


def build_parser() -> argparse.ArgumentParser:
    """Flags del script. `studio narration tts` los usa para validar y mostrar la ayuda."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        '--model',
        choices=ENGINES,
        default='voxcpm2',
        help='TTS engine (default voxcpm2; see server/data/narration/README.md)',
    )
    ap.add_argument('--ref', type=Path, default=paths.REFERENCE, help='folder of references or one .wav file')
    ap.add_argument(
        '--voice',
        choices=list(approved_voices(STYLES)),
        help='free voice from the catalog, approved in every style (uv run studio narration voices); replaces --ref',
    )
    ap.add_argument('--style', choices=STYLES, help='default: the "style" in the JSON, or expert')
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument('--text', help='text to narrate, in quotes')
    source.add_argument('--file', type=Path, nargs='+', help='one or more .txt or .json files; the model loads once')
    ap.add_argument(
        '--output',
        type=Path,
        help='with one script, the .wav; with several, the folder. Default out/narration/',
    )
    ap.add_argument('--batch', type=int, help='sentences per pass in Qwen; default based on free VRAM')
    ap.add_argument('--seed', type=int, help='base seed; default random. It is printed and saved in the .json')
    ap.add_argument(
        '--master',
        choices=['voice', 'no'],
        default='voice',
        help='voice: --lufs loudness with a 70 Hz high-pass, no compression unless the peak requires it; '
        'no: unprocessed',
    )
    ap.add_argument('--lufs', type=float, default=-16.0, help='target loudness for --master voice (default -16)')
    ap.add_argument(
        '--language',
        choices=['es', 'en'],
        default='es',
        help='engine and whisper language; with en, the default style is neutral-en',
    )
    ap.add_argument(
        '--evaluate',
        action='store_true',
        help='at the end transcribes each output with whisper and compares it, paragraph by paragraph, '
        'with the requested text',
    )
    ap.add_argument(
        '--retries',
        type=int,
        default=0,
        help='with --evaluate: rounds in which only paragraphs with observations are regenerated',
    )
    return ap

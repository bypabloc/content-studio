r"""Catálogo de voces libres para narrar sin grabarse: construye y aprueba cada voz.

Uso:
    uv run studio narration voices --list                # catálogo, licencia y estado de cada voz
    uv run studio narration voices --build yesid         # descarga, genera los 12 estilos y los aprueba
    uv run studio narration voices --build all --force

Cada voz del catálogo (server/data/narration/voices/catalog.json) parte de un clip real
de 8-12 s (o de varios clips cortos
del mismo hablante, unidos) con licencia de uso comercial: CC0 o dominio público, o una que pide MENCIÓN
(CC BY, CC BY-SA, Jenny). Mención = atribución: al publicar algo hecho con esa voz hay que dar crédito a su
autor, con el texto `atribucion` del catálogo (mencion(); docs/research/voces-libres-clonacion/12).
Ese clip, normalizado, es el estilo `neutral`. El resto de ESTILOS se genera con CosyVoice 3
(la misma voz leyendo el texto del kit de grabación, dirigido con una instrucción en inglés) y cada clip se
aprueba si conserva la voz (similitud de hablante con la base), se entiende (WER con whisper) y cumple los
criterios de referencia de docs/scripts/README.md. Una voz entra en `narration tts --voice` solo si aprueba TODOS los
estilos. Resultado: server/data/narration/voices/<voz>/<estilo>.wav + .txt y aprobacion.json (gitignoreados).
Investigación y mediciones: docs/research/voces-libres-clonacion/.
"""

from __future__ import annotations

import argparse
import sys

from content_studio.common import process
from content_studio.narration.engines.registry import ENGINES
from content_studio.narration.styles import STYLES
from content_studio.narration.voices.build import build
from content_studio.narration.voices.catalog import catalog, mention, state


def build_parser() -> argparse.ArgumentParser:
    """Parser de `python -m content_studio.narration.voices.main`."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()  # sin flags equivale a --list
    g.add_argument('--list', action='store_true', help='shows the catalog and the status of each voice (default)')
    g.add_argument('--build', nargs='+', metavar='REFERENCE', help='voices to build and approve, or "all"')
    ap.add_argument('--force', action='store_true', help='regenerate everything even if it exists')
    return ap


def main() -> None:
    """Entrada del catálogo de voces: lista o construye."""
    a = build_parser().parse_args()
    cat = catalog()
    if not a.build:
        for name, f in cat.items():
            print(f'{name:<16} {f["language"]} · {f["license"]} · {f["description"]}')
            print(f'{"":<16} {state(name, STYLES)}')
            if m := mention(f):
                print(f'{"":<16} required credit: {m}')
        return
    names = list(cat) if a.build == ['all'] else a.build
    if unknown := [n for n in names if n not in cat]:
        sys.exit(f'Unknown voice: {", ".join(unknown)}. Options: {", ".join(cat)}')
    # se relanza en el venv de CosyVoice
    process.use_venv(
        ENGINES['cosyvoice3'].path_venv(),
        'server/data/narration/README.md',
        module='content_studio.narration.voices.main',
    )
    print(
        f'Notice: the styles are generated with CosyVoice 3 ({ENGINES["cosyvoice3"].license}). '
        'Ver docs/research/voces-libres-clonacion/02.'
    )
    results = {n: build(n, cat[n], a.force) for n in names}
    sys.exit(0 if all(results.values()) else 1)


if __name__ == '__main__':
    main()

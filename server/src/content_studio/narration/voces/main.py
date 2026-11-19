r"""Catálogo de voces libres para narrar sin grabarse: construye y aprueba cada voz.

Uso:
    python cli.py narration voces --listar                 # catálogo, licencia y estado de cada voz
    python cli.py narration voces --construir yesid        # descarga, genera los 12 estilos y los aprueba
    python cli.py narration voces --construir todas --forzar

Cada voz del catálogo (server/data/narration/voces/catalogo.json) parte de un clip real
de 8-12 s (o de varios clips cortos
del mismo hablante, unidos) con licencia de uso comercial: CC0 o dominio público, o una que pide MENCIÓN
(CC BY, CC BY-SA, Jenny). Mención = atribución: al publicar algo hecho con esa voz hay que dar crédito a su
autor, con el texto `atribucion` del catálogo (mencion(); docs/research/voces-libres-clonacion/12).
Ese clip, normalizado, es el estilo `neutral`. El resto de ESTILOS se genera con CosyVoice 3
(la misma voz leyendo el texto del kit de grabación, dirigido con una instrucción en inglés) y cada clip se
aprueba si conserva la voz (similitud de hablante con la base), se entiende (WER con whisper) y cumple los
criterios de referencia de docs/guiones/README.md. Una voz entra en `narration tts --voz` solo si aprueba TODOS los
estilos. Resultado: server/data/narration/voces/<voz>/<estilo>.wav + .txt y aprobacion.json (gitignoreados).
Investigación y mediciones: docs/research/voces-libres-clonacion/.
"""

from __future__ import annotations

import argparse
import sys

from content_studio.comun import proceso
from content_studio.narration.estilos import ESTILOS
from content_studio.narration.motores.registro import MOTORES
from content_studio.narration.voces.catalogo import catalogo, estado, mencion
from content_studio.narration.voces.construir import construir


def construir_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()  # sin flags (p. ej. desde el menú de cli.py) equivale a --listar
    g.add_argument('--listar', action='store_true', help='muestra el catálogo y el estado de cada voz (por defecto)')
    g.add_argument('--construir', nargs='+', metavar='VOZ', help='voces a construir y aprobar, o "todas"')
    ap.add_argument('--forzar', action='store_true', help='regenera todo aunque ya exista')
    return ap


def main() -> None:
    a = construir_parser().parse_args()
    cat = catalogo()
    if not a.construir:
        for nombre, f in cat.items():
            print(f'{nombre:<16} {f["idioma"]} · {f["licencia"]} · {f["descripcion"]}')
            print(f'{"":<16} {estado(nombre, ESTILOS)}')
            if m := mencion(f):
                print(f'{"":<16} mención obligatoria: {m}')
        return
    nombres = list(cat) if a.construir == ['todas'] else a.construir
    if desconocidas := [n for n in nombres if n not in cat]:
        sys.exit(f'Voz desconocida: {", ".join(desconocidas)}. Opciones: {", ".join(cat)}')
    # se relanza en el venv de CosyVoice
    proceso.usar_venv(
        MOTORES['cosyvoice3'].ruta_venv(),
        'server/data/narration/README.md',
        modulo='content_studio.narration.voces.main',
    )
    print(
        f'Aviso: los estilos se generan con CosyVoice 3 ({MOTORES["cosyvoice3"].licencia}). '
        'Ver docs/research/voces-libres-clonacion/02.'
    )
    resultados = {n: construir(n, cat[n], a.forzar) for n in nombres}
    sys.exit(0 if all(resultados.values()) else 1)


if __name__ == '__main__':
    main()

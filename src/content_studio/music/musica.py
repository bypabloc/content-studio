"""main() de music: valida en el python del usuario, se relanza en el venv del motor y genera las pistas.

Directo: PYTHONPATH=src python -m content_studio.music.musica --modelo acestep --estilo lofi-chill
"""

from __future__ import annotations

import re
import sys
import unicodedata

from content_studio.comun import proceso
from content_studio.music.evaluacion import con_voz, liberar_gpu
from content_studio.music.motores.base import Trabajos
from content_studio.music.parser import ESTILOS, MODELOS, construir_parser


def resolver_estilo(
    valor: str, tono: str | None = None, bpm: int | None = None, compas: str | None = None
) -> tuple[str, dict]:
    """Devuelve (nombre de archivo, estilo). Los flags pisan los metadatos del preset;
    el texto libre sirve de caption y de tags, y exige tono y bpm.

    >>> resolver_estilo('ambient')[1]['tono'], resolver_estilo('ambient', tono='Am', bpm=60)[1]['bpm']
    ('D Major', 60)
    >>> nombre, e = resolver_estilo('Synthwave, retro 80s!', tono='E Minor', bpm=105)
    >>> nombre, e['tags'], e['tono'], e['bpm'], e['compas']
    ('synthwave-retro-80s', 'Synthwave, retro 80s!', 'E Minor', 105, '4')
    >>> resolver_estilo('Música épica', tono='C Major', bpm=90)[0], resolver_estilo('¡¿?!', tono='C Major', bpm=90)[0]
    ('musica-epica', 'libre')
    >>> resolver_estilo('bossa nova')
    Traceback (most recent call last):
    SystemExit: "bossa nova" no es un preset: define --tono y --bpm (ej. --tono "C Major" --bpm 90)
    """
    if valor in ESTILOS:
        nombre, base = valor, ESTILOS[valor]
    else:
        if tono is None or bpm is None:
            sys.exit(f'"{valor}" no es un preset: define --tono y --bpm (ej. --tono "C Major" --bpm 90)')
        ascii_ = unicodedata.normalize('NFKD', valor.lower()).encode('ascii', 'ignore').decode()  # música → musica
        nombre = re.sub(r'[^a-z0-9]+', '-', ascii_).strip('-')[:60] or 'libre'
        base = dict(caption=valor, tags=valor, compas='4')
    pisar = {k: v for k, v in dict(tono=tono, bpm=bpm, compas=compas).items() if v is not None}
    return nombre, {**base, **pisar}


def main() -> None:
    proceso.consola_utf8()  # cp1252 (Windows, a una tubería) no tiene ≤ ni –: que no reviente el --help
    ap = construir_parser()
    a = ap.parse_args()
    espec = MODELOS[a.modelo]
    if a.reintentos and not a.evaluar:
        ap.error('--reintentos necesita --evaluar')
    if a.evaluar and not espec.evalua:
        ap.error('--evaluar solo está en el venv de acestep (ahí está demucs)')
    if a.variantes < 1:
        ap.error('--variantes debe ser 1 o más')

    # Validar antes de relanzar en el venv y cargar el modelo.
    trabajos = []
    for valor in a.estilo:
        nombre, estilo = resolver_estilo(valor, a.tono, a.bpm, a.compas)
        for i in range(1, a.variantes + 1):
            sufijo = f'-v{i}' if a.variantes > 1 else ''
            trabajos.append((estilo, (a.carpeta / f'{a.modelo}-{nombre}{sufijo}.wav').resolve()))

    proceso.usar_venv(espec.ruta_venv(), 'music/README.md', modulo='content_studio.music.musica')
    a.carpeta.mkdir(parents=True, exist_ok=True)
    motor = espec.crear()

    def generar(lista: Trabajos) -> None:
        for _, salida in lista:  # si el motor falla, no queda la pista de una corrida anterior como si fuera nueva
            salida.unlink(missing_ok=True)
        motor.generar(lista, a)

    generar(trabajos)
    if not a.evaluar:
        faltan = [s.name for _, s in trabajos if not s.exists()]
        if faltan:
            sys.exit(f'No se generaron: {", ".join(faltan)}')
        return

    liberar_gpu()
    pendientes = con_voz([t[1] for t in trabajos])
    for _ in range(a.reintentos):
        if not pendientes:
            break
        print(f'Regenerando {len(pendientes)} pista(s) con voz...', flush=True)
        generar([t for t in trabajos if t[1] in pendientes])
        liberar_gpu()
        pendientes = con_voz(pendientes)
    print(f'{len(trabajos) - len(pendientes)}/{len(trabajos)} pistas sin voz')
    if pendientes:
        sys.exit(f'Con voz tras los reintentos: {", ".join(p.name for p in pendientes)}')


if __name__ == '__main__':
    main()

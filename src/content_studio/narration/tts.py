"""main() de narration tts: valida en el python del usuario, se relanza en el venv del motor y narra cada guion.

Directo: PYTHONPATH=src python -m content_studio.narration.tts --modelo voxcpm2 --voz karen-savage --texto "..."
Flags y formato del guion: content_studio/narration/parser.py.
"""

from __future__ import annotations

import random

from content_studio import rutas
from content_studio.comun import proceso
from content_studio.narration.guion import avisar_sobrescritura, guiones, planificar
from content_studio.narration.metadatos import avisos_voz, guardar_metadatos
from content_studio.narration.parser import ESTILOS, MOTORES, aprobadas, construir_parser
from content_studio.narration.pipeline import evaluar, lote_auto, narrar


def main() -> None:
    ap = construir_parser()
    a = ap.parse_args()
    if a.reintentos and not a.evaluar:
        ap.error('--reintentos necesita --evaluar')
    if a.voz:
        ficha = aprobadas(ESTILOS)[a.voz]
        if ficha['idioma'] != a.idioma:
            ap.error(f'la voz {a.voz} es en "{ficha["idioma"]}": usa --idioma {ficha["idioma"]}')
        a.ref = rutas.VOCES / a.voz

    trabajos = planificar(a, guiones(a))  # valida estilos y rutas antes de relanzar y de cargar el modelo

    e = MOTORES[a.modelo]
    # Desde aquí corre en el venv del motor: los avisos se imprimen una sola vez.
    proceso.usar_venv(e.ruta_venv(), 'narration/README.md', modulo='content_studio.narration.tts')
    if a.voz:
        avisos_voz(a.voz, aprobadas(ESTILOS)[a.voz])
    avisar_sobrescritura(trabajos)

    import torch

    motor = e.crear()
    lote = a.lote or (lote_auto(torch.cuda.mem_get_info()[0] / 2**30, e.pesos) if e.lote else 1)
    semilla = a.semilla if a.semilla is not None else random.randrange(2**31)
    print(f'Semilla: {semilla}')
    if not e.comercial:
        print(f'Aviso: {a.modelo} tiene licencia no comercial ({e.licencia}). Solo uso personal.')
    elif 'academic' in e.licencia:
        print(
            f'Aviso: {a.modelo} es Apache-2.0, pero su model card dice "for academic purposes only" (sin aclarar). '
            'Ver docs/research/voicestudio-narracion/07.'
        )

    resultados = [
        narrar(motor, texto, estilo, a.ref, salida, lote, semilla, idioma=a.idioma, master=a.master, lufs=a.lufs)
        for texto, estilo, salida in trabajos
    ]

    if a.evaluar:
        evaluar(motor, resultados, lote, semilla, a.reintentos, a.idioma)
    elif motor.sugerir_evaluar:
        print(f'Sugerencia: usa --evaluar con {a.modelo}')
    for g in resultados:
        guardar_metadatos(motor, g)


if __name__ == '__main__':
    main()

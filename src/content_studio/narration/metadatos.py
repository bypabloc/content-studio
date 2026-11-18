"""El .json de cada toma (lo necesario para reproducirla) y los avisos de licencia de las voces del catálogo."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path

from content_studio import rutas
from content_studio.narration.motores.base import MotorTTS
from content_studio.narration.voces.catalogo import catalogo, mencion


def avisos_voz(nombre: str, ficha: dict) -> None:
    """Lo que hay que saber antes de publicar una narración con una voz del catálogo: permiso del dueño y mención."""
    if not ficha.get('consentimiento'):
        print(
            f'Aviso: la voz {nombre} ({ficha["fuente"]}) tiene licencia {ficha["licencia"]}, pero su dueño no dio '
            'permiso para clonarla (regla 5 de AGENTS.md). Uso personal; para uso comercial, pídele permiso o usa '
            'una voz con consentimiento. Ver docs/research/voces-libres-clonacion/02.'
        )
    if m := mencion(ficha):
        print(
            f'MENCIÓN OBLIGATORIA ({ficha["licencia"]}): pon este crédito en la descripción del video. '
            'Queda en el .json.'
        )
        print(f'  {m}')
    if 'BY-SA' in ficha['licencia']:
        print(
            'Aviso: licencia "compartir igual" (BY-SA). No pongas el clip original en el video, y si alguien '
            'considera la narración una adaptación, tendría que publicarse con la misma licencia. Ver '
            'docs/research/voces-libres-clonacion/12.'
        )


def voz_de_referencia(ref: Path) -> dict | None:
    """Ficha del catálogo de la voz a la que pertenece una referencia (narration/voces/<voz>/<estilo>.wav), o None."""
    ref = Path(ref).resolve()
    if ref.parent.parent != rutas.VOCES.resolve():
        return None
    ficha = catalogo().get(ref.parent.name)
    return ficha and {'voz': ref.parent.name, 'licencia': ficha['licencia'], 'fuente': ficha['fuente'],
                      'consentimiento': ficha.get('consentimiento', False), 'mencion': mencion(ficha)}  # fmt: skip


def sha256(ruta) -> str:
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def version_tts() -> str:
    """Commit del script; con '-dirty' si hay cambios sin confirmar (la toma no sería reproducible con ese commit)."""
    r = subprocess.run(
        ['git', 'describe', '--always', '--dirty', '--abbrev=7'], cwd=rutas.RAIZ, capture_output=True, text=True
    )
    return r.stdout.strip() or 'desconocida'


def guardar_metadatos(motor: MotorTTS, g: dict) -> None:
    """Escribe <salida>.json con lo necesario para reproducir la toma: motor, semillas, referencias y bloques."""
    import torch

    e = motor.espec
    hashes: dict[Path, str] = {}
    bloques = []
    for i, (b, pb, (_, ini, fin)) in enumerate(zip(g['segs'], g['pb'], g['bloques'], strict=False)):
        if pb['ref'] not in hashes:
            hashes[pb['ref']] = sha256(pb['ref'])
        bloques.append({
            'i': i + 1, 'texto_guion': b['texto'], 'texto_enviado': pb['enviar'], 'estilo': pb['estilo'],
            'referencia': str(pb['ref']), 'referencia_sha256': hashes[pb['ref']],
            'emocion': pb['emocion'], 'modo': pb['modo'], 'pausa_despues': b['pausa'],
            'inicio_s': round(ini, 3), 'fin_s': round(fin, 3), 'semilla': g['semilla_bloque'][i],
            'avisos': pb['avisos'],
        })  # fmt: skip
    meta = {
        'version_tts': version_tts(), 'fecha': datetime.now().astimezone().isoformat(timespec='seconds'),
        'motor': e.nombre, 'licencia': e.licencia, 'comercial': e.comercial, 'idioma': g['idioma'],
        'semilla': g['semilla'], 'semillas_por_ronda': g['semillas'], 'bloques': bloques,
        'master': g['master_info'], 'evaluacion': g.get('evaluacion'),
        'parametros': {**g['p'], **motor.params},
        'tiempo_generacion_s': round(g['tiempo_s'], 1), 'duracion_s': round(g['bloques'][-1][2], 2),
        'vram_pico_gib': round(torch.cuda.max_memory_reserved() / 2**30, 2),
        # Voces del catálogo usadas en la toma, con la mención que pide su licencia (para la descripción del video).
        'voces': list({v['voz']: v for pb in g['pb'] if (v := voz_de_referencia(pb['ref']))}.values()) or None,
    }  # fmt: skip
    g['salida'].with_suffix('.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')

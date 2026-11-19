"""Los comandos de narration: tts, grabar y voces."""

from __future__ import annotations

from types import ModuleType

from content_studio import paths
from content_studio.cli.commands.base import Command, Option


class Tts(Command):
    clave = 'narration tts'
    module = 'content_studio.narration.tts'
    parser = 'content_studio.narration.parser'
    icono = '🎙'
    titulo = 'Narrar un texto o guion'
    desc = 'Voz clonada en español neutro · 7 motores'
    help = '🎙  Narrar un texto o guion (content_studio.narration.tts). Sin flags abre el asistente.'
    assistant = True

    def catalog(self, mod: ModuleType) -> dict[str, list[Option]]:
        from content_studio.narration.voices import catalog as cv

        models = []
        for name, m in mod.ENGINES.items():
            parts = [m.note] if m.note else []
            parts += [m.license, 'uso comercial' if m.commercial else 'NO comercial']
            if m.weights is not None:
                parts.append(f'{m.weights:.1f} GB')
            models.append(Option(name, ' · '.join(parts), None if m.installed() else 'no instalado'))
        recorded = '● referencia grabada'
        styles = [
            Option(e, recorded if (paths.REFERENCE / f'{e}.wav').exists() else '○ sin grabar: indica --ref')
            for e in mod.STYLES
        ]
        voices = []
        for n, f in cv.catalog().items():
            est = cv.state(n, mod.STYLES)
            mention = ' · pide mención' if cv.mention(f) else ''
            reason = None if est == 'approved' else f'{est}: python cli.py narration voces --build {n}'
            voices.append(Option(n, f'{f["language"]} · {f["license"]}{mention} · {f["description"]}', reason))
        return {'model': models, 'style': styles, 'voice': voices}


class Record(Command):
    clave = 'narration grabar'
    module = parser = 'content_studio.narration.grabar.main'
    icono = '🎤'
    titulo = 'Grabar voces de referencia'
    desc = 'Graba, mide y normaliza server/data/narration/reference/<estilo>.wav'
    help = '🎤  Grabar las voces de referencia (content_studio.narration.grabar).'

    def state(self) -> list[str]:
        txt = list(paths.REFERENCE.glob('*.txt'))
        recorded = sum((paths.REFERENCE / f'{t.stem}.wav').exists() for t in txt)
        return [f'voces de referencia [{"green" if recorded else "yellow"}]{recorded}/{len(txt)}[/]']


class Voices(Command):
    clave = 'narration voces'
    module = parser = 'content_studio.narration.voices.main'
    icono = '🗣'
    titulo = 'Voces libres del catálogo'
    desc = 'Construye y aprueba voces CC0 o de dominio público'
    help = '🗣  Construir y aprobar las voces libres del catálogo (content_studio.narration.voices).'

    def state(self) -> list[str]:
        from content_studio.narration.styles import STYLES
        from content_studio.narration.voices.catalog import approved_voices, catalog

        free = len(approved_voices(STYLES))
        return [f'voces libres [{"green" if free else "yellow"}]{free}/{len(catalog())}[/]']

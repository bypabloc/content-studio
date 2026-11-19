"""Los comandos de narration: tts, grabar y voces."""

from __future__ import annotations

from types import ModuleType

from content_studio import paths
from content_studio.cli.commands.base import Command, Option


class Tts(Command):
    """Comando `narration tts`: narración con clonación de voz."""

    key = 'narration tts'
    module = 'content_studio.narration.tts'
    parser = 'content_studio.narration.parser'
    icon = '🎙'
    title = 'Narrate a text or script'
    desc = 'Cloned voice, neutral Spanish · 7 engines'
    help = '🎙  Narrate a text or script (content_studio.narration.tts). Without flags, opens the assistant.'
    assistant = True

    def catalog(self, mod: ModuleType) -> dict[str, list[Option]]:
        """Motores y voces de narración para el asistente."""
        from content_studio.narration.voices import catalog as cv

        models = []
        for name, m in mod.ENGINES.items():
            parts = [m.note] if m.note else []
            parts += [m.license, 'commercial use' if m.commercial else 'NOT commercial']
            if m.weights is not None:
                parts.append(f'{m.weights:.1f} GB')
            models.append(Option(name, ' · '.join(parts), None if m.installed() else 'not installed'))
        recorded = '● recorded reference'
        styles = [
            Option(e, recorded if (paths.REFERENCE / f'{e}.wav').exists() else '○ not recorded: pass --ref')
            for e in mod.STYLES
        ]
        voices = []
        for n, f in cv.catalog().items():
            est = cv.state(n, mod.STYLES)
            mention = ' · requires credit' if cv.mention(f) else ''
            reason = None if est == 'approved' else f'{est}: python cli.py narration voces --build {n}'
            voices.append(Option(n, f'{f["language"]} · {f["license"]}{mention} · {f["description"]}', reason))
        return {'model': models, 'style': styles, 'voice': voices}


class Record(Command):
    # cspell:ignore grabar: nombre del paquete narration/grabar/, que traduce la 007 (D-3)
    """Comando `narration grabar`: graba las voces de referencia."""

    key = 'narration grabar'
    module = parser = 'content_studio.narration.grabar.main'
    icon = '🎤'
    title = 'Record reference voices'
    desc = 'Records, measures and normalizes server/data/narration/reference/<style>.wav'
    help = '🎤  Record the reference voices (content_studio.narration.grabar).'

    def state(self) -> list[str]:
        """Estado de las voces de referencia grabadas, para el menú."""
        txt = list(paths.REFERENCE.glob('*.txt'))
        recorded = sum((paths.REFERENCE / f'{t.stem}.wav').exists() for t in txt)
        return [f'reference voices [{"green" if recorded else "yellow"}]{recorded}/{len(txt)}[/]']


class Voices(Command):
    """Comando `narration voces`: voces libres del catálogo."""

    key = 'narration voces'
    module = parser = 'content_studio.narration.voices.main'
    icon = '🗣'
    title = 'Free voices from the catalog'
    desc = 'Builds and approves CC0 or public-domain voices'
    help = '🗣  Build and approve the free voices in the catalog (content_studio.narration.voices).'

    def state(self) -> list[str]:
        """Cantidad de voces libres aprobadas, para el menú."""
        from content_studio.narration.styles import STYLES
        from content_studio.narration.voices.catalog import approved_voices, catalog

        free = len(approved_voices(STYLES))
        return [f'free voices [{"green" if free else "yellow"}]{free}/{len(catalog())}[/]']

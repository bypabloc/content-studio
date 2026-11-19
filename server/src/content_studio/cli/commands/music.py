"""El comando music."""

from __future__ import annotations

from types import ModuleType

from content_studio.cli.commands.base import Command, Option


class Music(Command):
    clave = 'music'
    module = 'content_studio.music.music_main'
    parser = 'content_studio.music.parser'
    icono = '🎵'
    titulo = 'Generar música de fondo'
    desc = 'Instrumental con ACE-Step 1.5 o HeartMuLa'
    help = '🎵  Generar música instrumental (content_studio.music). Sin flags abre el asistente.'
    assistant = True

    def catalog(self, mod: ModuleType) -> dict[str, list[Option]]:
        models = [Option(n, e.desc, None if e.installed() else 'no instalado') for n, e in mod.MODELS.items()]
        styles = [
            Option(n, f'{e["key"]} · {e["bpm"]} BPM · {e.get("time_signature", "4")}/4') for n, e in mod.STYLES.items()
        ]
        return {'model': models, 'style': styles}

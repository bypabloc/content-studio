"""El comando music."""

from __future__ import annotations

from types import ModuleType

from content_studio.cli.commands.base import Command, Option


class Music(Command):
    """Comando `music`: genera música de fondo."""

    key = 'music'
    module = 'content_studio.music.music_main'
    parser = 'content_studio.music.parser'
    icon = '🎵'
    title = 'Generate background music'
    desc = 'Instrumental con ACE-Step 1.5 o HeartMuLa'
    help = '🎵  Generate instrumental music (content_studio.music). Without flags, opens the assistant.'
    assistant = True

    def catalog(self, mod: ModuleType) -> dict[str, list[Option]]:
        """Modelos y estilos de música para el asistente."""
        models = [Option(n, e.desc, None if e.installed() else 'not installed') for n, e in mod.MODELS.items()]
        styles = [
            Option(n, f'{e["key"]} · {e["bpm"]} BPM · {e.get("time_signature", "4")}/4') for n, e in mod.STYLES.items()
        ]
        return {'model': models, 'style': styles}

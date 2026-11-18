"""El comando music."""

from __future__ import annotations

from types import ModuleType

from content_studio.cli.comandos.base import Comando, Opcion


class Musica(Comando):
    clave = 'music'
    modulo = 'content_studio.music.musica'
    parser = 'content_studio.music.parser'
    icono = '🎵'
    titulo = 'Generar música de fondo'
    desc = 'Instrumental con ACE-Step 1.5 o HeartMuLa'
    ayuda = '🎵  Generar música instrumental (content_studio.music). Sin flags abre el asistente.'
    asistente = True

    def catalogo(self, mod: ModuleType) -> dict[str, list[Opcion]]:
        modelos = [Opcion(n, e.desc, None if e.instalado() else 'no instalado') for n, e in mod.MODELOS.items()]
        estilos = [
            Opcion(n, f'{e["tono"]} · {e["bpm"]} BPM · {e.get("compas", "4")}/4') for n, e in mod.ESTILOS.items()
        ]
        return {'modelo': modelos, 'estilo': estilos}

"""Los comandos de narration: tts, grabar y voces."""

from __future__ import annotations

from content_studio import rutas
from content_studio.cli.comandos.base import Comando, Opcion


class Tts(Comando):
    clave = 'narration tts'
    modulo = 'content_studio.narration.tts'
    parser = 'content_studio.narration.parser'
    icono = '🎙'
    titulo = 'Narrar un texto o guion'
    desc = 'Voz clonada en español neutro · 7 motores'
    ayuda = '🎙  Narrar un texto o guion (narration/tts.py). Sin flags abre el asistente.'
    asistente = True

    def catalogo(self, mod) -> dict[str, list[Opcion]]:
        from content_studio.narration.voces import catalogo as cv

        modelos = []
        for nombre, m in mod.MOTORES.items():
            partes = [m.nota] if m.nota else []
            partes += [m.licencia, 'uso comercial' if m.comercial else 'NO comercial']
            if m.pesos is not None:
                partes.append(f'{m.pesos:.1f} GB')
            modelos.append(Opcion(nombre, ' · '.join(partes), None if m.instalado() else 'no instalado'))
        grabada = '● referencia grabada'
        estilos = [
            Opcion(e, grabada if (rutas.VOZ / f'{e}.wav').exists() else '○ sin grabar: indica --ref')
            for e in mod.ESTILOS
        ]
        voces = []
        for n, f in cv.catalogo().items():
            est = cv.estado(n, mod.ESTILOS)
            mencion = ' · pide mención' if cv.mencion(f) else ''
            motivo = None if est == 'aprobada' else f'{est}: python cli.py narration voces --construir {n}'
            voces.append(Opcion(n, f'{f["idioma"]} · {f["licencia"]}{mencion} · {f["descripcion"]}', motivo))
        return {'modelo': modelos, 'estilo': estilos, 'voz': voces}


class Grabar(Comando):
    clave = 'narration grabar'
    modulo = parser = 'content_studio.narration.grabar.main'
    icono = '🎤'
    titulo = 'Grabar voces de referencia'
    desc = 'Graba, mide y normaliza narration/voz/<estilo>.wav'
    ayuda = '🎤  Grabar las voces de referencia (narration/grabar.py).'

    def estado(self) -> list[str]:
        txt = list(rutas.VOZ.glob('*.txt'))
        grabadas = sum((rutas.VOZ / f'{t.stem}.wav').exists() for t in txt)
        return [f'voces de referencia [{"green" if grabadas else "yellow"}]{grabadas}/{len(txt)}[/]']


class Voces(Comando):
    clave = 'narration voces'
    modulo = parser = 'content_studio.narration.voces.main'
    icono = '🗣'
    titulo = 'Voces libres del catálogo'
    desc = 'Construye y aprueba voces CC0 o de dominio público'
    ayuda = '🗣  Construir y aprobar las voces libres del catálogo (narration/voces.py).'

    def estado(self) -> list[str]:
        from content_studio.narration.estilos import ESTILOS
        from content_studio.narration.voces.catalogo import aprobadas, catalogo

        libres = len(aprobadas(ESTILOS))
        return [f'voces libres [{"green" if libres else "yellow"}]{libres}/{len(catalogo())}[/]']

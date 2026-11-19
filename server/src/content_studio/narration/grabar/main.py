r"""Graba las voces de referencia (server/data/narration/voz/<estilo>.wav) desde un dispositivo de audio del equipo.

Uso:
    python cli.py narration grabar --listar                # dispositivos de audio disponibles
    python cli.py narration grabar                         # elige dispositivo y estilos en el menú
    python cli.py narration grabar --dispositivo RDPSource --estilo neutral amistosa
    python cli.py narration grabar --dispositivo 2 --todos # el kit completo, en el orden de la guía

Mientras graba muestra el texto, el tiempo contra la duración de la guía, el nivel y la forma de onda.
Cada toma se guarda en server/data/narration/voz/tomas/ (gitignoreado). Al aceptar una, se recortan los bordes a 0.4 s,
se normaliza a -18 LUFS (limitando solo los picos) y queda en
server/data/narration/voz/<estilo>.wav (WAV mono, 48 kHz, 24 bits).
Después se verifica con los criterios de docs/guiones/README.md. Usa ffmpeg, ffprobe y ffplay (escuchar).
"""

from __future__ import annotations

import argparse
import contextlib
import shutil
import subprocess
import sys

import questionary
from questionary import Choice, Separator
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from content_studio.comun.archivos import siguiente_numero
from content_studio.narration.grabar.dispositivos import WINDOWS, fuentes
from content_studio.narration.grabar.interfaz import ACENTO, ESTILO_Q, console, ficha_toma
from content_studio.narration.grabar.kit import DURACION, GUION, KIT, OPCIONAL, nivel_toma
from content_studio.narration.grabar.toma import grabar_toma
from content_studio.narration.referencia import medir, procesar, verificar
from content_studio.rutas import RAIZ, TOMAS, VOZ


def elegir_fuente(lista: list[tuple[str, str, bool]], pedida: str | None) -> str:
    """Nombre de la fuente: la pedida (por nombre o por número) o la que se elige en el menú."""
    if pedida is None:
        predet = next((n for n, _, p in lista if p), lista[0][0])
        return questionary.select(
            'Micrófono', style=ESTILO_Q, instruction='(↑↓ · enter)', default=predet,
            choices=[Choice([('', f'{n:<20}'), ('class:desc', d + ('  · predeterminado' if p else ''))], value=n)
                     for n, d, p in lista],
        ).unsafe_ask()  # fmt: skip
    if pedida.isdigit() and 1 <= int(pedida) <= len(lista):
        return lista[int(pedida) - 1][0]
    if any(nombre == pedida for nombre, _, _ in lista):
        return pedida
    sys.exit(f'No hay un dispositivo "{pedida}". Ver: python cli.py narration grabar --listar')


def elegir_estilos() -> list[str]:
    """Casillas con el estado de cada referencia. Vienen marcadas las pendientes del kit."""

    def opcion(n: str, opcional: bool) -> Choice:
        lo, hi = DURACION[n]
        hecha = (VOZ / f'{n}.wav').exists()
        estado = ('● grabada (se reemplaza)' if hecha else '○ pendiente') + ('  · opcional' if opcional else '')
        texto = [('', f'{n:<13}'), ('class:desc', f'{lo:>2}–{hi} s   {estado}')]
        return Choice(texto, value=n, checked=not hecha and not opcional)

    elegidos = questionary.checkbox(
        'Referencias a grabar', style=ESTILO_Q, instruction='(espacio marca · a todas · enter confirma)',
        choices=[*[opcion(n, False) for n, _, _ in KIT], Separator('  ' + '─' * 30),
                 *[opcion(n, True) for n, _, _ in OPCIONAL]],
        validate=lambda x: bool(x) or 'Marca al menos una',
        erase_when_done=True,  # su respuesta ("done (n selections)") va en inglés: se escribe la propia
    ).unsafe_ask()  # fmt: skip
    console.print(f'[bold {ACENTO}]?[/] [bold]Referencias a grabar[/] [green]{", ".join(elegidos)}[/]')
    return elegidos


def grabar_estilo(fuente: str, estilo: str, sobrescribir: bool, i: int, total: int) -> str:
    """Graba las tomas de un estilo hasta aceptar una, que se procesa y se verifica. Devuelve el resultado."""
    final = VOZ / f'{estilo}.wav'
    if final.exists() and not sobrescribir:
        pregunta = questionary.confirm(f'{estilo} ya está grabada. ¿Reemplazarla?', default=False, style=ESTILO_Q)
        if not pregunta.unsafe_ask():
            return 'ya existía'
    lo, hi = DURACION[estilo]
    texto = (VOZ / f'{estilo}.txt').read_text(encoding='utf-8').strip()
    ficha_estilo = Panel(
        Group(Text(texto, style='bold'), Text(''),
              Text.from_markup(f'[dim]Duración {lo}–{hi} s · actitud en '
                               f'server/data/narration/docs/guiones/{GUION[estilo]}\n'
                               'Graba 3 tomas seguidas y quédate con la más natural, no con la más actuada.[/]')),
        title=f'[bold {ACENTO}]{estilo}[/] [dim]· {i}/{total} · {fuente}[/]', title_align='left',
        border_style=ACENTO, padding=(1, 2))  # fmt: skip
    TOMAS.mkdir(parents=True, exist_ok=True)
    n = siguiente_numero(TOMAS, estilo)
    escuchar = shutil.which('ffplay')
    previa = None  # ficha de la toma anterior, para compararla con la siguiente
    while True:
        console.clear()  # una pantalla por toma: el panel en vivo necesita el alto completo
        console.print(ficha_estilo)
        if previa:
            console.print(previa)
        toma = TOMAS / f'{estilo}-{n}.wav'
        opciones = [Choice('●  Grabar', 'grabar'), Choice('↷  Saltar este estilo', 'saltar')]
        eleccion = questionary.select(f'Toma {n}', style=ESTILO_Q, instruction='(↑↓ · enter)', choices=opciones)
        if eleccion.unsafe_ask() == 'saltar':
            return 'saltada'
        ok, niveles = grabar_toma(fuente, toma, estilo, n, texto)
        console.clear()
        console.print(ficha_estilo)
        if not ok:
            previa = Text.from_markup(
                f'[yellow]⚠ Toma {n} sin audio:[/] se paró antes de capturar o el dispositivo no entrega datos.'
            )
            toma.unlink(missing_ok=True)
            n += 1
            continue
        m = medir(toma)
        nivel = nivel_toma(m['pico'])
        previa = ficha_toma(n, m, estilo, niveles)
        console.print(previa)
        while True:
            accion = questionary.select('¿Qué hacemos con esta toma?', style=ESTILO_Q, instruction='(↑↓ · enter)',
                                        default='usar' if nivel == 'ok' else 'otra', choices=[
                Choice('✓  Usarla como referencia', 'usar', disabled='no se oye nada' if nivel == 'silencio' else None),
                Choice('▶  Escucharla', 'escuchar', disabled=None if escuchar else 'falta ffplay'),
                Choice('↻  Grabar otra toma', 'otra'),
                Choice('↷  Saltar este estilo', 'saltar')]).unsafe_ask()  # fmt: skip
            if accion != 'escuchar':
                break
            with (
                console.status('Reproduciendo… (Ctrl+C para cortar)', spinner='dots'),
                contextlib.suppress(KeyboardInterrupt),
            ):
                subprocess.run([escuchar, '-nodisp', '-autoexit', '-loglevel', 'quiet', str(toma)])
        if accion == 'saltar':
            return 'saltada'
        if accion == 'usar':
            with console.status('Recortando, normalizando y verificando…', spinner='dots'):
                procesar(toma, final)
                checks = verificar(final, *DURACION[estilo])
            t = Table(box=None, padding=(0, 1), show_header=False)
            for cumple, detalle in checks:
                t.add_row(Text('✓' if cumple else '✗', style='green' if cumple else 'red'), detalle)
            todo = all(c for c, _ in checks)
            titulo = f'[bold]{"✓" if todo else "⚠"} {final.relative_to(RAIZ).as_posix()}[/]'
            borde = 'green' if todo else 'yellow'
            console.print(Panel(t, title=titulo, title_align='left', border_style=borde, padding=(0, 2)))
            return 'lista' if todo else 'lista con observaciones'
        n += 1


def construir_parser() -> argparse.ArgumentParser:
    """Flags del script. cli.py lo usa para mostrar la ayuda."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--listar', action='store_true', help='muestra los dispositivos de audio disponibles y sale')
    ap.add_argument('--dispositivo', help='nombre de la fuente (p. ej. RDPSource) o su número en --listar')
    ap.add_argument('--estilo', nargs='+', choices=list(DURACION), metavar='ESTILO',
                    help='referencias a grabar, p. ej. neutral amistosa (ver docs/guiones/README.md)')  # fmt: skip
    ap.add_argument('--todos', action='store_true', help='graba el kit completo en el orden de la guía')
    ap.add_argument('--sobrescribir', action='store_true', help='reemplaza las referencias que ya existen')
    return ap


def listar(lista: list[tuple[str, str, bool]]) -> None:
    t = Table(title='Dispositivos de audio', title_style=f'bold {ACENTO}', header_style='bold', border_style='grey35')
    t.add_column('#', justify='right', style='dim')
    t.add_column('Nombre (--dispositivo)', style='bold cyan')
    t.add_column('Descripción')
    t.add_column('')
    for i, (nombre, desc, pred) in enumerate(lista, 1):
        t.add_row(str(i), nombre, desc, '[green]● predeterminado[/]' if pred else '')
    console.print(t)


def main() -> None:
    a = construir_parser().parse_args()
    lista = fuentes()
    if not lista:
        sys.exit(
            'No hay micrófonos activos en el registro de Windows (MMDevices/Audio/Capture).'
            if WINDOWS
            else 'No hay fuentes de audio de PulseAudio o PipeWire (ffmpeg -sources pulse no devolvió nada).'
        )
    if a.listar:
        listar(lista)
        return
    if not sys.stdin.isatty():
        sys.exit('Grabar necesita una terminal interactiva.')
    resultados = []
    try:
        bienvenida = Text.from_markup(
            f'[bold {ACENTO}]🎤  Grabar voces de referencia[/]\n[dim]Se guardan en server/data/narration/voz/. '
            'Usa audífonos y un cuarto en silencio.[/]'
        )
        console.print(Panel(bienvenida, border_style=ACENTO, padding=(0, 2), expand=False))
        fuente = elegir_fuente(lista, a.dispositivo)
        interactivo = not (a.todos or a.estilo)
        estilos = [n for n, _, _ in KIT] if a.todos else (a.estilo or elegir_estilos())
        for i, estilo in enumerate(estilos, 1):
            resultados.append((estilo, grabar_estilo(fuente, estilo, a.sobrescribir or interactivo, i, len(estilos))))
    except (KeyboardInterrupt, EOFError):
        console.print('\n[dim]Cancelado. Las tomas grabadas siguen en server/data/narration/voz/tomas/.[/]')
    if resultados:
        color = {'lista': 'green', 'lista con observaciones': 'yellow'}
        t = Table(title='Resumen', title_style=f'bold {ACENTO}', border_style='grey35', header_style='bold')
        t.add_column('Estilo', style='bold')
        t.add_column('Resultado')
        for estilo, r in resultados:
            t.add_row(estilo, f'[{color.get(r, "dim")}]{r}[/]')
        console.print(t)


if __name__ == '__main__':
    main()

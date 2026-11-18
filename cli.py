#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["typer>=0.29", "rich>=14", "questionary>=2.1"]
# ///
"""Punto de entrada único: python cli.py [<herramienta> <comando> [flags]].

    python cli.py                                   # menú interactivo
    python cli.py narration tts                     # asistente: pregunta lo que falte
    python cli.py narration tts --modelo qwen-0.6b --texto "..."   # completo: se ejecuta directo
    python cli.py narration grabar
    python cli.py music --modelo acestep --estilo lofi-chill

Los flags pasan tal cual al script de cada herramienta, que sigue relanzándose en su venv.
Si falta un flag obligatorio o uno es inválido, el asistente lo pide en vez de fallar (solo en una
terminal: sin TTY se ejecuta tal cual, para scripts y agentes). Si este python no tiene las
dependencias, el CLI se relanza con `uv run --script` (las lee del bloque de arriba).
"""

import argparse
import glob
import importlib.util
import os
import re
import shlex
import signal
import subprocess
import sys
from pathlib import Path


def relanzar(args: list[str]) -> None:
    """os.exec*. En Windows no reemplaza el proceso (el padre sale y la terminal vuelve al prompt con el
    hijo corriendo), así que ahí se espera al hijo, que se queda con el Ctrl+C."""
    sys.stdout.flush()
    if os.name == 'nt':
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        sys.exit(subprocess.call(args))
    os.execvp(args[0], args)


try:
    import questionary
    import typer
    from questionary import Choice, Separator
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except ImportError:
    try:
        relanzar(['uv', 'run', '--quiet', '--script', __file__, *sys.argv[1:]])
    except FileNotFoundError:
        sys.exit('Falta uv (o instala typer, rich y questionary en este python). Ver "Requisitos" en AGENTS.md.')

for _f in (sys.stdout, sys.stderr):  # cp1252 (Windows, a una tubería) no tiene los íconos: que no reviente
    _f.reconfigure(errors='replace')
RAIZ = Path(__file__).resolve().parent
console = Console(highlight=False)
ACENTO = '#a78bfa'
ESTILO = questionary.Style([
    ('qmark', f'fg:{ACENTO} bold'), ('question', 'bold'), ('answer', 'fg:#34d399 bold'),
    ('pointer', f'fg:{ACENTO} bold'), ('highlighted', f'fg:{ACENTO} bold'), ('selected', 'fg:#34d399'),
    ('instruction', 'fg:#6b7280 italic'), ('separator', 'fg:#4b5563'), ('disabled', 'fg:#6b7280 italic'),
    ('desc', 'fg:#9ca3af'),
])
SEPARADOR = '  ' + '─' * 30
COMANDOS = {
    'narration tts': dict(script='narration/tts.py', icono='🎙', titulo='Narrar un texto o guion',
                          desc='Voz clonada en español neutro · 7 motores', asistente=True),
    'narration grabar': dict(script='narration/grabar.py', icono='🎤', titulo='Grabar voces de referencia',
                             desc='Graba, mide y normaliza narration/voz/<estilo>.wav', asistente=False),
    'narration voces': dict(script='narration/voces.py', icono='🗣', titulo='Voces libres del catálogo',
                            desc='Construye y aprueba voces CC0 o de dominio público', asistente=False),
    'music': dict(script='music/musica.py', icono='🎵', titulo='Generar música de fondo',
                  desc='Instrumental con ACE-Step 1.5 o HeartMuLa', asistente=True),
}


# ── Carga de los scripts ─────────────────────────────────────────────────────────────────────────
def cargar(script: str):
    """Importa el script (sus imports de arriba son solo stdlib) para leer su parser y catálogos."""
    ruta = RAIZ / script
    sys.path.insert(0, str(ruta.parent))
    spec = importlib.util.spec_from_file_location(f'_cli_{ruta.stem}', ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def catalogo(clave: str, mod) -> dict[str, list[tuple[str, str, str | None]]]:
    """Por flag: (valor, descripción, motivo si está deshabilitado) para describir las opciones en los menús."""
    if clave == 'narration tts':
        voz = RAIZ / 'narration' / 'voz'
        modelos = []
        for nombre, m in mod.MOTORES.items():
            partes = [m['nota']] if 'nota' in m else []
            partes += [m['licencia'], 'uso comercial' if m['comercial'] else 'NO comercial']
            if 'pesos' in m:
                partes.append(f'{m["pesos"]:.1f} GB')
            instalado = (RAIZ / 'narration' / m['venv']).exists()
            modelos.append((nombre, ' · '.join(partes), None if instalado else 'no instalado'))
        estilos = [(e, '● referencia grabada' if (voz / f'{e}.wav').exists() else '○ sin grabar: indica --ref', None)
                   for e in mod.ESTILOS]
        import voces as catalogo_voces  # cargar() dejó narration/ en sys.path
        voces = []
        for n, f in catalogo_voces.catalogo().items():
            est = catalogo_voces.estado(n, mod.ESTILOS)
            mencion = ' · pide mención' if catalogo_voces.mencion(f) else ''
            voces.append((n, f'{f["idioma"]} · {f["licencia"]}{mencion} · {f["descripcion"]}',
                          None if est == 'aprobada' else f'{est}: python cli.py narration voces --construir {n}'))
        return {'modelo': modelos, 'estilo': estilos, 'voz': voces}
    if clave == 'music':
        modelos = [(n, 'recomendado · ~30 s por pista' if n == 'acestep' else 'lento · ~5 min por pista',
                    None if (RAIZ / 'music' / v).exists() else 'no instalado') for n, v in mod.MODELOS.items()]
        estilos = [(n, f'{e["tono"]} · {e["bpm"]} BPM · {e.get("compas", "4")}/4', None) for n, e in mod.ESTILOS.items()]
        return {'modelo': modelos, 'estilo': estilos}
    return {}


def flags(ap: argparse.ArgumentParser) -> list[argparse.Action]:
    return [a for a in ap._actions if a.option_strings and not isinstance(a, argparse._HelpAction)]


def unir(args: list[str]) -> str:
    """Comando para mostrar, con las comillas del shell de este sistema (shlex.join pone comillas posix)."""
    return subprocess.list2cmdline(args) if os.name == 'nt' else shlex.join(args)


def partir(texto: str) -> list[str]:
    r"""Rutas escritas en una línea. Si el texto entero es una ruta que existe (aunque tenga espacios), es una sola.
    En Windows sin el modo posix, que se come las \ (D:\a.json salía D:a.json), y sin las comillas."""
    if Path(texto.strip()).exists():
        return [texto.strip()]
    if os.name != 'nt':
        return shlex.split(texto)
    return [t[1:-1] if len(t) > 1 and t[0] == t[-1] and t[0] in '"\'' else t for t in shlex.split(texto, posix=False)]


def vacio(v) -> bool:
    """Sin valor: None, False o lista vacía. Con `in (None, False, [])` se perdía el 0, porque 0 == False."""
    return v is None or v is False or (isinstance(v, list) and not v)


def obligatorio(acc: argparse.Action, ap: argparse.ArgumentParser) -> bool:
    return acc.required or any(g.required and acc in g._group_actions for g in ap._mutually_exclusive_groups)


# ── Ayuda ────────────────────────────────────────────────────────────────────────────────────────
def ayuda(clave: str) -> None:
    cmd = COMANDOS[clave]
    mod = cargar(cmd['script'])
    ap = mod.construir_parser()
    resumen = (mod.__doc__ or '').strip().split('\n\n')[0]
    t = Table(box=None, padding=(0, 2), show_header=True, header_style=f'bold {ACENTO}')
    t.add_column('Flag', style='bold cyan', no_wrap=True)
    t.add_column('Valores', style='green', max_width=28)
    t.add_column('Defecto', style='dim', max_width=14)
    t.add_column('Descripción', ratio=1, overflow='fold')
    for acc in flags(ap):
        if isinstance(acc, argparse._StoreTrueAction):
            valores = 'sí/no'
        elif acc.choices:
            valores = ' · '.join(map(str, acc.choices))
        else:
            valores = (acc.metavar or (acc.type.__name__ if acc.type else 'texto')).lower()
        if acc.nargs in ('+', '*'):
            valores += ' (varios)'
        defecto = acc.default
        if isinstance(defecto, Path):
            defecto = os.path.relpath(defecto, RAIZ)
        elif isinstance(defecto, list):
            defecto = ' '.join(map(str, defecto))
        marca = ' [red]*[/]' if obligatorio(acc, ap) else ''
        t.add_row(', '.join(acc.option_strings) + marca, valores,
                  '' if vacio(defecto) else str(defecto), acc.help or '')
    console.print(Panel(
        Group(Text(resumen, style='italic'), Text(''), t, Text(''),
              Text.from_markup('[red]*[/] obligatorio · si falta, el asistente lo pregunta · '
                               f'[bold]python cli.py {clave}[/] sin flags abre el asistente')),
        title=f'{cmd["icono"]}  [bold]{clave}[/] — {cmd["titulo"]}', title_align='left', border_style=ACENTO,
        padding=(1, 2)))


# ── Asistente ────────────────────────────────────────────────────────────────────────────────────
class ErrorArgs(Exception):
    pass


def leer(ap: argparse.ArgumentParser, args: list[str]) -> tuple[dict, list[str]]:
    """Flags válidos que vinieron en `args` (dest -> valor), sin exigir los obligatorios. Un flag inválido
    se descarta con su valor (y se avisa) para conservar el resto."""
    def error(msg):
        raise ErrorArgs(msg)
    ap.error = error
    for acc in flags(ap):
        acc.required = False
    for g in ap._mutually_exclusive_groups:
        g.required = False
    avisos = []
    while True:
        try:
            ns, sobra = ap.parse_known_args(args)
            break
        except ErrorArgs as e:
            m = re.search(r'argument (-[-\w]+)', str(e))
            # El token puede venir como --flag=valor o abreviado (--mod): el error de argparse cita el flag completo.
            i = next((k for k, t in enumerate(args) if t.startswith('-') and m and (
                (c := t.split('=', 1)[0]) == m[1] or (len(c) > 2 and m[1].startswith(c)))), None)
            if i is None:
                return {}, [str(e)]
            j = i + 1
            while '=' not in args[i] and j < len(args) and not args[j].startswith('--'):
                j += 1
            avisos.append(f'{unir(args[i:j])} no es válido; lo eliges abajo')
            args = args[:i] + args[j:]
    if sobra:
        avisos.append(f'no reconocido: {unir(sobra)}')
    dados = {acc.dest: getattr(ns, acc.dest) for acc in flags(ap)
             if any(t == o or t.startswith(o + '=') for t in args for o in acc.option_strings)}
    return dados, avisos


def a_argv(ap: argparse.ArgumentParser, valores: dict) -> list[str]:
    argv = []
    for acc in flags(ap):
        if acc.dest not in valores or vacio(valores[acc.dest]):
            continue
        v = valores[acc.dest]
        if isinstance(acc, argparse._StoreTrueAction):
            argv.append(acc.option_strings[0])
        elif isinstance(v, list):
            argv += [acc.option_strings[0], *map(str, v)]
        else:
            argv += [acc.option_strings[0], str(v)]
    return argv


def validar(mod, argv: list[str]) -> str | None:
    """Error del parser real del script con estos flags, o None."""
    ap = mod.construir_parser()
    ap.error = lambda msg: (_ for _ in ()).throw(ErrorArgs(msg))
    try:
        ap.parse_args(argv)
    except ErrorArgs as e:
        return str(e)
    return None


def titulo(valor: str, desc: str, ancho: int = 16, plano: bool = False):
    """Valor y descripción en columnas. `plano`: texto sin estilos, que es lo único que el filtro de
    búsqueda de questionary sabe filtrar (con tuplas de estilo falla)."""
    if plano:
        return f'{valor:<{ancho}}{desc}'
    return [('', f'{valor:<{ancho}}'), ('class:desc', desc)]


def preguntar(acc: argparse.Action, cat: dict, actual):
    """Pide un flag según su tipo: casilla, lista, ruta con autocompletado o texto validado."""
    msg = acc.dest.replace('_', ' ').capitalize()
    pista = f'{acc.option_strings[0]}' + (f' · {acc.help}' if acc.help else '')
    pista = pista if len(pista) <= 80 else pista[:79] + '…'
    opciones = cat.get(acc.dest)
    ancho = max((len(v) for v, _, _ in opciones or []), default=14) + 2
    filtro = dict(use_search_filter=True, use_jk_keys=False) if len(opciones or []) > 15 else {}
    if filtro:
        pista += '  · escribe para filtrar'
    if isinstance(acc, argparse._StoreTrueAction):
        return questionary.confirm(msg, default=bool(actual), style=ESTILO, instruction=f'({pista}) ').unsafe_ask()
    varios = acc.nargs in ('+', '*')
    if opciones is None and acc.choices:
        opciones = [(str(c), '', None) for c in acc.choices]
    if opciones:
        if varios:
            marcados = set(actual or [])
            elegidos = questionary.checkbox(
                msg, style=ESTILO, **filtro, erase_when_done=True,  # la respuesta "done (n selections)" va en inglés
                instruction=f'{acc.option_strings[0]}{"  · escribe para filtrar" if filtro else ""}'
                            '  · espacio marca · enter confirma',
                choices=[Choice(titulo(v, d, ancho, bool(filtro)), value=v, disabled=dis, checked=v in marcados)
                         for v, d, dis in opciones],
            ).unsafe_ask()
            console.print(f'[bold {ACENTO}]?[/] [bold]{msg}[/] [green]{", ".join(elegidos) or "—"}[/]')
            if not acc.choices:  # sin choices fijos (estilo de music): también acepta texto libre
                libre = questionary.text('Texto libre adicional (enter para omitir):', style=ESTILO).unsafe_ask()
                elegidos += [libre] if libre.strip() else []
            return elegidos or None
        validos = [v for v, _, dis in opciones if not dis]
        extra = [] if acc.required else [Separator(SEPARADOR), Choice('↺  Por defecto (sin indicar)', value=None)]
        return questionary.select(
            msg, style=ESTILO, use_shortcuts=False, instruction=pista, **filtro,
            default=actual if actual in validos else (validos[0] if validos else None),
            choices=[*[Choice(titulo(v, d, ancho, bool(filtro)), value=v, disabled=dis)
                       for v, d, dis in opciones], *extra],
        ).unsafe_ask()
    if acc.type is Path:
        console.print(f'[dim]  {pista}{" · admite comodines: guiones/*.json" if varios else ""} · tab completa[/]')
        texto = questionary.path(msg, style=ESTILO,
                                 default=str(actual[0] if isinstance(actual, list) else actual or '')).unsafe_ask()
        rutas = [Path(r) for p in partir(texto) for r in (sorted(glob.glob(p)) or [p])]
        return (rutas or None) if varios else (rutas[0] if rutas else None)

    def valido(t: str):
        if not t.strip():
            return True
        try:
            acc.type(t) if acc.type else t
            return True
        except ValueError:
            return f'Debe ser {acc.type.__name__}'
    texto = questionary.text(msg, style=ESTILO, validate=valido, instruction=pista + ' · vacío = por defecto',
                             default='' if actual is None else str(actual)).unsafe_ask().strip()
    if not texto:
        return None
    return acc.type(texto) if acc.type else texto


def resumen(ap, valores: dict, clave: str) -> Panel:
    t = Table(box=None, padding=(0, 2), show_header=False)
    t.add_column(style='bold cyan', no_wrap=True)
    t.add_column(ratio=1)
    for acc in flags(ap):
        dado = acc.dest in valores and not vacio(valores[acc.dest])
        v = valores[acc.dest] if dado else acc.default
        if vacio(v):
            continue
        v = 'sí' if v is True else ' '.join(map(str, v)) if isinstance(v, list) else (
            os.path.relpath(v, RAIZ) if isinstance(v, Path) and v.is_absolute() else str(v))
        v = v if len(v) < 300 else v[:297] + '…'
        t.add_row(Text(acc.option_strings[0], style='bold cyan' if dado else 'dim'),
                  Text(v, style='green') if dado else Text.assemble((v, 'dim'), ('  por defecto', 'dim italic')))
    comando = unir(['python', 'cli.py', *clave.split(), *a_argv(ap, valores)])
    return Panel(Group(t, Text(''), Text('$ ' + comando, style='dim')),
                 title=f'{COMANDOS[clave]["icono"]}  [bold]{clave}[/]', title_align='left',
                 border_style=ACENTO, padding=(1, 2))


def asistente(clave: str, args: list[str], forzar: bool = False) -> None:
    cmd = COMANDOS[clave]
    mod = cargar(cmd['script'])
    ap = mod.construir_parser()
    if not forzar and validar(mod, args) is None:
        lanzar(clave, args)
    valores, avisos = leer(mod.construir_parser(), args)
    for aviso in avisos:
        console.print(f'[yellow]⚠ {aviso}[/]')
    cat = catalogo(clave, mod)
    console.print(f'\n{cmd["icono"]}  [bold]{cmd["titulo"]}[/]  [dim]{cmd["desc"]}[/]\n')

    # 1. Los obligatorios que faltan, en el orden del parser. Un grupo excluyente es una elección previa.
    for acc in flags(ap):
        grupo = next((g for g in ap._mutually_exclusive_groups if g.required and acc in g._group_actions), None)
        if grupo:
            if any(valores.get(a.dest) is not None for a in grupo._group_actions):
                continue
            acc = questionary.select(
                '¿De dónde sale el contenido?', style=ESTILO, instruction='(↑↓ · enter)',
                choices=[Choice(titulo(a.option_strings[0], a.help or ''), value=a) for a in grupo._group_actions],
            ).unsafe_ask()
        elif not acc.required or valores.get(acc.dest) is not None:
            continue
        valores[acc.dest] = preguntar(acc, cat, None)

    # 2. Bucle: resumen editable hasta ejecutar, redibujado en su lugar.
    while True:
        console.clear()
        console.print(resumen(ap, valores, clave))
        argv = a_argv(ap, valores)
        error = validar(mod, argv)
        if error:
            console.print(f'[red]✗ {error}[/]')
        accion = questionary.select(
            '¿Qué hacemos?', style=ESTILO, instruction='(↑↓ · enter)',
            choices=[Choice('▶  Ejecutar', 'ejecutar', disabled='corrige el error' if error else None),
                     Choice('✎  Agregar o cambiar una opción', 'editar'),
                     Choice('✕  Cancelar', 'cancelar')],
        ).unsafe_ask()
        if accion == 'ejecutar':
            lanzar(clave, argv)
        if accion == 'cancelar':
            cancelar()
        opciones = []
        for acc in flags(ap):
            v = valores.get(acc.dest)
            estado = ('✓ ' + (' '.join(map(str, v)) if isinstance(v, list) else 'sí' if v is True else str(v))
                      if not vacio(v) else (acc.help or ''))
            opciones.append(Choice(titulo(acc.option_strings[0], estado[:90]), value=acc))
        acc = questionary.select('¿Qué opción?', choices=[*opciones, Separator(SEPARADOR), Choice('↩  Volver', None)],
                                 style=ESTILO, instruction='(↑↓ · enter)').unsafe_ask()
        if acc is not None:
            valores[acc.dest] = preguntar(acc, cat, valores.get(acc.dest))
            for g in ap._mutually_exclusive_groups:  # --archivo reemplaza a --texto y viceversa
                if acc in g._group_actions and valores[acc.dest] is not None:
                    for otro in g._group_actions:
                        if otro is not acc:
                            valores.pop(otro.dest, None)


# ── Lanzar ───────────────────────────────────────────────────────────────────────────────────────
def lanzar(clave: str, args: list[str]) -> None:
    if sys.stdout.isatty():
        console.rule(f'[bold {ACENTO}]{COMANDOS[clave]["icono"]}  {clave}[/] [dim]{unir(args)}[/]',
                     align='left', style=ACENTO)
    relanzar([sys.executable, str(RAIZ / COMANDOS[clave]['script']), *args])


def cancelar() -> None:
    console.print('[dim]✕ Cancelado.[/]')
    raise typer.Exit(130)


def ejecutar(clave: str, args: list[str]) -> None:
    if '-h' in args or '--help' in args:
        return ayuda(clave)
    if COMANDOS[clave]['asistente'] and sys.stdin.isatty() and sys.stdout.isatty():
        try:
            asistente(clave, args)
        except KeyboardInterrupt:  # Ctrl+C en una pregunta; sin esto Click imprime "Aborted!"
            cancelar()
    lanzar(clave, args)


# ── Menú principal ───────────────────────────────────────────────────────────────────────────────
def estado() -> Text:
    """Una línea con la GPU libre y las referencias grabadas: lo que importa antes de elegir."""
    partes = []
    try:
        usada, total = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5).stdout.split('\n')[0].split(',')
        libre = (int(total) - int(usada)) / 1024
        color = 'green' if libre > 5 else 'yellow' if libre > 3 else 'red'
        partes.append(f'GPU [{color}]{libre:.1f} GB libres[/] de {int(total) / 1024:.0f} GB')
    except (OSError, ValueError, subprocess.TimeoutExpired):
        partes.append('[dim]GPU no detectada[/]')
    voz = RAIZ / 'narration' / 'voz'
    grabadas = sum((voz / f'{t.stem}.wav').exists() for t in voz.glob('*.txt'))
    partes.append(f'voces de referencia [{"green" if grabadas else "yellow"}]{grabadas}/{len(list(voz.glob("*.txt")))}[/]')
    tts = cargar(COMANDOS['narration tts']['script'])
    libres = len(tts.aprobadas(tts.ESTILOS))
    import voces as catalogo_voces
    partes.append(f'voces libres [{"green" if libres else "yellow"}]{libres}/{len(catalogo_voces.catalogo())}[/]')
    return Text.from_markup('  ·  '.join(partes))


def menu() -> None:
    console.print(Panel(
        Group(Text.from_markup(f'[bold {ACENTO}]content-studio[/]  [dim]audio local para videos[/]'), estado()),
        border_style=ACENTO, padding=(0, 2), expand=False))
    try:
        clave = questionary.select(
            '¿Qué quieres hacer?', style=ESTILO, instruction='(↑↓ · enter · Ctrl+C sale)',
            choices=[Choice([('', f'{c["icono"]}  {c["titulo"]:<28}'), ('class:desc', c['desc'])], value=k)
                     for k, c in COMANDOS.items()],
        ).unsafe_ask()
        if COMANDOS[clave]['asistente']:
            asistente(clave, [], forzar=True)
    except KeyboardInterrupt:
        cancelar()
    lanzar(clave, [])


# ── Typer ────────────────────────────────────────────────────────────────────────────────────────
PASO = dict(context_settings={'allow_extra_args': True, 'ignore_unknown_options': True}, add_help_option=False)
app = typer.Typer(help='Audio local para videos: narración y música. Sin argumentos abre el menú.',
                  add_completion=False, rich_markup_mode='rich')
narration = typer.Typer(help='Narración TTS clonando una voz (narration/README.md).', no_args_is_help=True)
app.add_typer(narration, name='narration')


@app.callback(invoke_without_command=True)
def raiz(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        if sys.stdin.isatty() and sys.stdout.isatty():
            menu()
        else:
            console.print(ctx.get_help())


@narration.command(**PASO)
def tts(ctx: typer.Context) -> None:
    """🎙  Narrar un texto o guion (narration/tts.py). Sin flags abre el asistente."""
    ejecutar('narration tts', ctx.args)


@narration.command(**PASO)
def grabar(ctx: typer.Context) -> None:
    """🎤  Grabar las voces de referencia (narration/grabar.py)."""
    ejecutar('narration grabar', ctx.args)


@narration.command(**PASO)
def voces(ctx: typer.Context) -> None:
    """🗣  Construir y aprobar las voces libres del catálogo (narration/voces.py)."""
    ejecutar('narration voces', ctx.args)


@app.command(**PASO)
def music(ctx: typer.Context) -> None:
    """🎵  Generar música instrumental (music/musica.py). Sin flags abre el asistente."""
    ejecutar('music', ctx.args)


if __name__ == '__main__':
    try:
        app()
    except KeyboardInterrupt:
        console.print('\n[dim]Cancelado.[/]')
        sys.exit(130)

"""Consola, estilo y preguntas de questionary según el tipo de cada flag."""

from __future__ import annotations

import argparse
import glob
from pathlib import Path
from typing import Any

import questionary
from questionary import Choice, Separator
from rich.console import Console

from content_studio.cli.args import es_booleano
from content_studio.common.process import split

console = Console(highlight=False)
ACCENT = '#a78bfa'
STYLE = questionary.Style(
    [
        ('qmark', f'fg:{ACCENT} bold'),
        ('question', 'bold'),
        ('answer', 'fg:#34d399 bold'),
        ('pointer', f'fg:{ACCENT} bold'),
        ('highlighted', f'fg:{ACCENT} bold'),
        ('selected', 'fg:#34d399'),
        ('instruction', 'fg:#6b7280 italic'),
        ('separator', 'fg:#4b5563'),
        ('disabled', 'fg:#6b7280 italic'),
        ('desc', 'fg:#9ca3af'),
    ]
)
SEPARATOR = '  ' + '─' * 30


def titulo(value: str, desc: str, width: int = 16, flat: bool = False) -> str | list[tuple[str, str]]:
    """Valor y descripción en columnas. `plano`: texto sin estilos, que es lo único que el filtro de
    búsqueda de questionary sabe filtrar (con tuplas de estilo falla)."""
    if flat:
        return f'{value:<{width}}{desc}'
    return [('', f'{value:<{width}}'), ('class:desc', desc)]


def _items(acc: argparse.Action, msg: str, pista: str, options: list, current: Any, several: bool) -> Any:
    """Casillas (varios valores) o lista de una opción, con filtro si son muchas."""
    width = max((len(v) for v, _, _ in options), default=14) + 2
    search = dict(use_search_filter=True, use_jk_keys=False) if len(options) > 15 else {}
    if search:
        pista += '  · escribe para filtrar'
    if several:
        marked = set(current or [])
        chosen = questionary.checkbox(
            msg,
            style=STYLE,
            **search,
            erase_when_done=True,  # la respuesta "done (n selections)" va en inglés
            instruction=f'{acc.option_strings[0]}{"  · escribe para filtrar" if search else ""}'
            '  · espacio marca · enter confirma',
            choices=[
                Choice(titulo(v, d, width, bool(search)), value=v, disabled=dis, checked=v in marked)
                for v, d, dis in options
            ],
        ).unsafe_ask()
        console.print(f'[bold {ACCENT}]?[/] [bold]{msg}[/] [green]{", ".join(chosen) or "—"}[/]')
        if not acc.choices:  # sin choices fijos (estilo de music): también acepta texto libre
            free = questionary.text('Texto libre adicional (enter para omitir):', style=STYLE).unsafe_ask()
            chosen += [free] if free.strip() else []
        return chosen or None
    valid = [v for v, _, dis in options if not dis]
    extra = [] if acc.required else [Separator(SEPARATOR), Choice('↺  Por defecto (sin indicar)', value=None)]
    return questionary.select(
        msg,
        style=STYLE,
        use_shortcuts=False,
        instruction=pista,
        **search,
        default=current if current in valid else (valid[0] if valid else None),
        choices=[*[Choice(titulo(v, d, width, bool(search)), value=v, disabled=dis) for v, d, dis in options], *extra],
    ).unsafe_ask()


def ask(acc: argparse.Action, cat: dict, current: Any) -> Any:
    """Pide un flag según su tipo: casilla, lista, ruta con autocompletado o texto validado."""
    msg = acc.dest.replace('_', ' ').capitalize()
    pista = f'{acc.option_strings[0]}' + (f' · {acc.help}' if acc.help else '')
    pista = pista if len(pista) <= 80 else pista[:79] + '…'
    if es_booleano(acc):
        return questionary.confirm(msg, default=bool(current), style=STYLE, instruction=f'({pista}) ').unsafe_ask()
    several = acc.nargs in ('+', '*')
    options = cat.get(acc.dest)
    if options is None and acc.choices:
        options = [(str(c), '', None) for c in acc.choices]
    if options:
        return _items(acc, msg, pista, options, current, several)
    if acc.type is Path:
        console.print(f'[dim]  {pista}{" · admite comodines: guiones/*.json" if several else ""} · tab completa[/]')
        default = str(current[0] if isinstance(current, list) else current or '')
        text = questionary.path(msg, style=STYLE, default=default).unsafe_ask()
        paths = [Path(r) for p in split(text) for r in (sorted(glob.glob(p)) or [p])]
        return (paths or None) if several else (paths[0] if paths else None)

    def valid(t: str):
        if not t.strip():
            return True
        try:
            acc.type(t) if acc.type else t
            return True
        except ValueError:
            return f'Debe ser {acc.type.__name__}'

    question = questionary.text(
        msg,
        style=STYLE,
        validate=valid,
        instruction=pista + ' · vacío = por defecto',
        default='' if current is None else str(current),
    )
    text = question.unsafe_ask().strip()
    if not text:
        return None
    return acc.type(text) if acc.type else text

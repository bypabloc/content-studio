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
from content_studio.comun.proceso import partir

console = Console(highlight=False)
ACENTO = '#a78bfa'
ESTILO = questionary.Style(
    [
        ('qmark', f'fg:{ACENTO} bold'),
        ('question', 'bold'),
        ('answer', 'fg:#34d399 bold'),
        ('pointer', f'fg:{ACENTO} bold'),
        ('highlighted', f'fg:{ACENTO} bold'),
        ('selected', 'fg:#34d399'),
        ('instruction', 'fg:#6b7280 italic'),
        ('separator', 'fg:#4b5563'),
        ('disabled', 'fg:#6b7280 italic'),
        ('desc', 'fg:#9ca3af'),
    ]
)
SEPARADOR = '  ' + '─' * 30


def titulo(valor: str, desc: str, ancho: int = 16, plano: bool = False) -> str | list[tuple[str, str]]:
    """Valor y descripción en columnas. `plano`: texto sin estilos, que es lo único que el filtro de
    búsqueda de questionary sabe filtrar (con tuplas de estilo falla)."""
    if plano:
        return f'{valor:<{ancho}}{desc}'
    return [('', f'{valor:<{ancho}}'), ('class:desc', desc)]


def _lista(acc: argparse.Action, msg: str, pista: str, opciones: list, actual: Any, varios: bool) -> Any:
    """Casillas (varios valores) o lista de una opción, con filtro si son muchas."""
    ancho = max((len(v) for v, _, _ in opciones), default=14) + 2
    filtro = dict(use_search_filter=True, use_jk_keys=False) if len(opciones) > 15 else {}
    if filtro:
        pista += '  · escribe para filtrar'
    if varios:
        marcados = set(actual or [])
        elegidos = questionary.checkbox(
            msg,
            style=ESTILO,
            **filtro,
            erase_when_done=True,  # la respuesta "done (n selections)" va en inglés
            instruction=f'{acc.option_strings[0]}{"  · escribe para filtrar" if filtro else ""}'
            '  · espacio marca · enter confirma',
            choices=[
                Choice(titulo(v, d, ancho, bool(filtro)), value=v, disabled=dis, checked=v in marcados)
                for v, d, dis in opciones
            ],
        ).unsafe_ask()
        console.print(f'[bold {ACENTO}]?[/] [bold]{msg}[/] [green]{", ".join(elegidos) or "—"}[/]')
        if not acc.choices:  # sin choices fijos (estilo de music): también acepta texto libre
            libre = questionary.text('Texto libre adicional (enter para omitir):', style=ESTILO).unsafe_ask()
            elegidos += [libre] if libre.strip() else []
        return elegidos or None
    validos = [v for v, _, dis in opciones if not dis]
    extra = [] if acc.required else [Separator(SEPARADOR), Choice('↺  Por defecto (sin indicar)', value=None)]
    return questionary.select(
        msg,
        style=ESTILO,
        use_shortcuts=False,
        instruction=pista,
        **filtro,
        default=actual if actual in validos else (validos[0] if validos else None),
        choices=[*[Choice(titulo(v, d, ancho, bool(filtro)), value=v, disabled=dis) for v, d, dis in opciones], *extra],
    ).unsafe_ask()


def preguntar(acc: argparse.Action, cat: dict, actual: Any) -> Any:
    """Pide un flag según su tipo: casilla, lista, ruta con autocompletado o texto validado."""
    msg = acc.dest.replace('_', ' ').capitalize()
    pista = f'{acc.option_strings[0]}' + (f' · {acc.help}' if acc.help else '')
    pista = pista if len(pista) <= 80 else pista[:79] + '…'
    if es_booleano(acc):
        return questionary.confirm(msg, default=bool(actual), style=ESTILO, instruction=f'({pista}) ').unsafe_ask()
    varios = acc.nargs in ('+', '*')
    opciones = cat.get(acc.dest)
    if opciones is None and acc.choices:
        opciones = [(str(c), '', None) for c in acc.choices]
    if opciones:
        return _lista(acc, msg, pista, opciones, actual, varios)
    if acc.type is Path:
        console.print(f'[dim]  {pista}{" · admite comodines: guiones/*.json" if varios else ""} · tab completa[/]')
        defecto = str(actual[0] if isinstance(actual, list) else actual or '')
        texto = questionary.path(msg, style=ESTILO, default=defecto).unsafe_ask()
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

    pregunta = questionary.text(
        msg,
        style=ESTILO,
        validate=valido,
        instruction=pista + ' · vacío = por defecto',
        default='' if actual is None else str(actual),
    )
    texto = pregunta.unsafe_ask().strip()
    if not texto:
        return None
    return acc.type(texto) if acc.type else texto

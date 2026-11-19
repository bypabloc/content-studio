"""Menú principal: la línea de estado (GPU y lo que aporta cada comando) y la elección del comando."""

from __future__ import annotations

import subprocess

import questionary
from questionary import Choice
from rich.console import Group
from rich.panel import Panel
from rich.text import Text

from content_studio.cli.comandos import REGISTRO
from content_studio.cli.flujo import asistente, cancelar, lanzar
from content_studio.cli.widgets import ACENTO, ESTILO, console


def gpu() -> str:
    try:
        consulta = ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits']
        salida = subprocess.run(consulta, capture_output=True, text=True, timeout=5).stdout
        usada, total = salida.split('\n')[0].split(',')
        libre = (int(total) - int(usada)) / 1024
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return '[dim]GPU no detectada[/]'
    color = 'green' if libre > 5 else 'yellow' if libre > 3 else 'red'
    return f'GPU [{color}]{libre:.1f} GB libres[/] de {int(total) / 1024:.0f} GB'


def estado() -> Text:
    """Una línea con la GPU libre y el estado de cada comando: lo que importa antes de elegir."""
    return Text.from_markup('  ·  '.join([gpu(), *(p for c in REGISTRO for p in c.estado())]))


def menu() -> None:
    cabecera = Text.from_markup(f'[bold {ACENTO}]content-studio[/]  [dim]audio local para videos[/]')
    console.print(Panel(Group(cabecera, estado()), border_style=ACENTO, padding=(0, 2), expand=False))
    try:
        cmd = questionary.select(
            '¿Qué quieres hacer?',
            style=ESTILO,
            instruction='(↑↓ · enter · Ctrl+C sale)',
            choices=[Choice([('', f'{c.icono}  {c.titulo:<28}'), ('class:desc', c.desc)], value=c) for c in REGISTRO],
        ).unsafe_ask()
        if cmd.asistente:
            asistente(cmd, [], forzar=True)
    except KeyboardInterrupt:
        cancelar()
    lanzar(cmd, [])

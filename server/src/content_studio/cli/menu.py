"""Menú principal: la línea de estado (GPU y lo que aporta cada comando) y la elección del comando."""

from __future__ import annotations

import subprocess

import questionary
from questionary import Choice
from rich.console import Group
from rich.panel import Panel
from rich.text import Text

from content_studio.cli.commands import REGISTRY
from content_studio.cli.flow import assistant, cancel, lanzar
from content_studio.cli.widgets import ACCENT, STYLE, console


def gpu() -> str:
    """VRAM usada y total de la GPU, o un texto si nvidia-smi no responde."""
    try:
        query = ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits']
        output = subprocess.run(query, capture_output=True, text=True, timeout=5).stdout
        used, total = output.split('\n')[0].split(',')
        free = (int(total) - int(used)) / 1024
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return '[dim]GPU no detectada[/]'
    color = 'green' if free > 5 else 'yellow' if free > 3 else 'red'
    return f'GPU [{color}]{free:.1f} GB libres[/] de {int(total) / 1024:.0f} GB'


def state() -> Text:
    """Una línea con la GPU libre y el estado de cada comando: lo que importa antes de elegir."""
    return Text.from_markup('  ·  '.join([gpu(), *(p for c in REGISTRY for p in c.state())]))


def menu() -> None:
    """Menú interactivo de la CLI, con el estado de la GPU y las voces."""
    header = Text.from_markup(f'[bold {ACCENT}]content-studio[/]  [dim]audio local para videos[/]')
    console.print(Panel(Group(header, state()), border_style=ACCENT, padding=(0, 2), expand=False))
    try:
        cmd = questionary.select(
            '¿Qué quieres hacer?',
            style=STYLE,
            instruction='(↑↓ · enter · Ctrl+C sale)',
            choices=[Choice([('', f'{c.icon}  {c.title:<28}'), ('class:desc', c.desc)], value=c) for c in REGISTRY],
        ).unsafe_ask()
        if cmd.assistant:
            assistant(cmd, [], force=True)
    except KeyboardInterrupt:
        cancel()
    lanzar(cmd, [])

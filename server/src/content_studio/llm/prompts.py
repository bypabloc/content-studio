"""Prompts de las tareas (spec 021, D-4): archivos .md con marcadores {{variable}}, en español."""

from __future__ import annotations

import re
from pathlib import Path

from content_studio import paths

DIRECTORY = Path(__file__).with_name('prompts')
MARKER = re.compile(r'\{\{(\w+)\}\}')
GUIDE = paths.DATA / 'narration/docs/formato-guion.md'
LAST_RULE = 22  # de la 23 en adelante son de proceso (JSON con visuales, evaluar, escuchar), no de escritura


def render(name: str, /, **values: object) -> str:
    """El prompt `name` con cada {{variable}} reemplazada; una variable sin valor es KeyError."""
    template = (DIRECTORY / f'{name}.md').read_text(encoding='utf-8')
    return MARKER.sub(lambda m: str(values[m.group(1)]), template)


def guide_rules() -> str:
    """Las reglas obligatorias de formato-guion.md (de la 1 a la 22), tal como están escritas."""
    section = GUIDE.read_text(encoding='utf-8').split('## Reglas obligatorias', 1)[1]
    rules = [line for line in section.splitlines() if re.match(r'\d+\. ', line)]
    return '\n'.join(line for line in rules if int(line.split('.', 1)[0]) <= LAST_RULE)

"""Instala una herramienta del sistema como trabajo de CPU."""

import json
import sys
from pathlib import Path

from content_studio.common import progress
from content_studio.system import tools

KIND = 'system.install_tool'
RESOURCE = 'cpu'


def validate(params: dict) -> list[dict]:
    """Restringe la instalación a la lista de herramientas admitidas."""
    if params.get('name') not in tuple(tools.PACKAGES):
        return [{'code': 'unknown_system_tool', 'params': {}}]
    return []


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Genera el comando de instalación para el worker."""
    return [sys.executable, '-m', __name__, params['name']]


def run(name: str) -> int:
    """Comprueba el resultado de winget y devuelve el código de salida."""
    progress.emit(0, 'installing')
    result = tools.install_tool(name)
    print(json.dumps(result))
    if not result['installed']:
        return 1
    progress.emit(1, 'detected')
    return 0


if __name__ == '__main__':
    sys.exit(run(sys.argv[1]))

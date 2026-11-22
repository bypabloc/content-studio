"""Desinstalación de las rutas que pertenecen a un motor administrado."""

import sys
from pathlib import Path

from content_studio import paths
from content_studio.engines import installer
from content_studio.services.engine_install import ERROR_CODES as _ERROR_CODES
from content_studio.services.engine_install import validate as validate_engine

KIND = 'engine.uninstall'
RESOURCE = 'cpu'
ERROR_CODES = _ERROR_CODES


def validate(params: dict) -> list[dict]:
    """El motor debe estar en el catálogo."""
    errors = validate_engine(params)
    if errors:
        return errors
    if not isinstance(params.get('force', False), bool):
        return [{'code': 'invalid_engine_action', 'params': {}}]
    return []


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Arma la desinstalación del motor."""
    return [sys.executable, '-m', __name__, params['engine'], *(['--force'] if params.get('force') else [])]


def run(engine: str, force: bool = False) -> int:
    """Borra la instalación de la app o devuelve un código de propietario externo."""
    try:
        installer.uninstall(engine, paths.engines_dir(), force=force)
    except installer.InstallError as error:
        print(error.code, file=sys.stderr)
        return installer.EXIT_CODES[error.code]
    return 0


if __name__ == '__main__':
    sys.exit(run(sys.argv[1], '--force' in sys.argv[2:]))

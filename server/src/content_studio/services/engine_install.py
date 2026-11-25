"""Instalación y reparación de motores como trabajos de CPU."""

from __future__ import annotations

import sys
from contextlib import closing
from pathlib import Path

from content_studio import credentials, paths
from content_studio.db import connection
from content_studio.engines import installer, recipes

KIND = 'engine.install'
RESOURCE = 'cpu'
ERROR_CODES = {code: detail for detail, code in installer.EXIT_CODES.items()}


def validate(params: dict) -> list[dict]:
    """La receta debe existir y la opción de reparación es booleana."""
    engine = params.get('engine')
    if (
        not isinstance(engine, str)
        or not recipes.ENGINE.fullmatch(engine)
        or not (recipes.DIRECTORY / f'{engine}.json').is_file()
    ):
        return [{'code': 'unknown_engine', 'params': {'model': engine}}]
    if not isinstance(params.get('repair', False), bool):
        return [{'code': 'invalid_engine_action', 'params': {}}]
    return []


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Arma el subproceso del motor seleccionado."""
    return [sys.executable, '-m', __name__, params['engine'], *(['--repair'] if params.get('repair') else [])]


def run(engine: str, repair: bool) -> int:
    """Verifica la licencia e instala en la raíz configurada."""
    try:
        recipe = recipes.load(engine)
        with closing(connection.connect(paths.db_path())) as conn:
            installer.check_license(conn, engine)
            token = credentials.huggingface_token(conn) if recipe.gated else None
        installer.install(recipe, paths.engines_dir(), repair, token=token)
    except installer.InstallError as error:
        print(error.code, file=sys.stderr)
        return installer.EXIT_CODES[error.code]
    return 0


if __name__ == '__main__':
    sys.exit(run(sys.argv[1], '--repair' in sys.argv[2:]))

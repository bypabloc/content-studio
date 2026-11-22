"""Trabajo de GPU que prueba un motor y guarda el resultado en settings."""

from __future__ import annotations

import json
import sys
from contextlib import closing
from pathlib import Path

from content_studio import paths
from content_studio.db import connection, settings
from content_studio.engines import verification
from content_studio.messages import t
from content_studio.services.engine_install import validate as validate_engine

KIND = 'engine.verify'
RESOURCE = 'gpu'
ERROR_CODES = {30: 'engine_not_installed', 31: 'engine_verify_failed'}


def validate(params: dict) -> list[dict]:
    """Valida que el motor exista en el catalogo de recetas."""
    return validate_engine(params)


def build_command(params: dict, output_dir: Path) -> list[str]:
    """Arma el comando del trabajo para el worker."""
    return [sys.executable, '-m', __name__, params['engine'], str(output_dir)]


def run(engine: str, output_dir: Path) -> int:
    """Ejecuta la prueba de humo y persiste el resultado, incluso si falla."""
    result = verification.verify_engine(engine, output_dir)
    with closing(connection.connect(paths.db_path())) as conn:
        settings.set_value(conn, f'engine.verify.{engine}', result)
        conn.commit()
    print(json.dumps(result, ensure_ascii=False))
    if result['ok']:
        return 0
    if result.get('error') == 'engine_not_installed':
        print(t('error.engine_not_installed', model=engine), file=sys.stderr)
        return 30
    print(t('error.engine_verify_failed'), file=sys.stderr)
    return 31


if __name__ == '__main__':
    sys.exit(run(sys.argv[1], Path(sys.argv[2])))

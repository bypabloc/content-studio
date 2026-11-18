"""python -m content_studio: el mismo CLI que python cli.py (hasta que el CLI viva en src/)."""

import runpy

from content_studio import rutas

runpy.run_path(str(rutas.RAIZ / 'cli.py'), run_name='__main__')

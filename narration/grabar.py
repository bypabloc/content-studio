# /// script
# requires-python = ">=3.10"
# dependencies = ["rich>=14", "questionary>=2.1"]
# ///
"""Shim temporal: el código vive en src/content_studio/narration/grabar/ (se borra al cerrar el refactor).

python narration/grabar.py ...  ==  PYTHONPATH=src python -m content_studio.narration.grabar.main ...
Sin rich o questionary en este python, se relanza con uv según la cabecera de arriba.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from content_studio.comun.proceso import relanzar  # noqa: E402

try:
    from content_studio.narration.grabar.main import main
except ImportError:  # python sin rich/questionary
    if __name__ == '__main__':
        relanzar(['uv', 'run', '--quiet', '--script', __file__, *sys.argv[1:]])
    raise

if __name__ == '__main__':
    main()

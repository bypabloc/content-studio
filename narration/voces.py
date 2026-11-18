"""Shim temporal: el código vive en src/content_studio/narration/voces/ (se borra al cerrar el refactor).

python narration/voces.py ...  ==  PYTHONPATH=src python -m content_studio.narration.voces.main ...
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from content_studio.narration.voces.main import main  # noqa: E402

if __name__ == '__main__':
    main()

"""Shim temporal: el código vive en src/content_studio/narration/ (se borra al cerrar el refactor).

python narration/tts.py ...  ==  PYTHONPATH=src python -m content_studio.narration.tts ...
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from content_studio.narration.tts import main  # noqa: E402

if __name__ == '__main__':
    main()

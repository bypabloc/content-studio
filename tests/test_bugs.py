"""Un test por bug corregido del análisis. Corre con: uv run --with pytest pytest tests"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(RAIZ / 'narration'), str(RAIZ / 'music')]


def test_tomas_max_mas_uno(tmp_path):
    from referencia import siguiente_numero

    assert siguiente_numero(tmp_path, 'neutral') == 1
    for n in ['neutral-1', 'neutral-3', 'neutral-en-7', 'neutral-fin-9', 'neutral-x']:
        (tmp_path / f'{n}.wav').touch()
    assert siguiente_numero(tmp_path, 'neutral') == 4  # contando daba 6, y con huecos pisaba una toma

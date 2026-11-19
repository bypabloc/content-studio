"""El código (server/src/ y lo que queda en server/data/narration/) se comporta igual que las
fixtures de server/tests/fixtures/."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'fixtures'))
import generar  # noqa: E402

FIXTURES = Path(generar.__file__).parent


def fixture(nombre: str) -> dict:
    return json.loads((FIXTURES / nombre).read_text(encoding='utf-8'))


def test_parsers_iguales_y_livianos(sin_pesadas):
    comandos, _ = generar.actual()
    assert generar.parsers(comandos) == fixture('parsers.json')


def test_bloques_iguales():
    _, tts = generar.actual()
    assert generar.bloques(tts) == fixture('bloques.json')

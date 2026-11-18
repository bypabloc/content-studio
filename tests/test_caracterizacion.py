"""El código (hoy el viejo de narration/ y music/) se comporta igual que las fixtures de tests/fixtures/."""

from __future__ import annotations

import doctest
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent / 'fixtures'))
import generar  # noqa: E402

FIXTURES = Path(generar.__file__).parent


def fixture(nombre: str) -> dict:
    return json.loads((FIXTURES / nombre).read_text(encoding='utf-8'))


def test_parsers_iguales_y_livianos(sin_pesadas):
    comandos, _ = generar.viejo()
    assert generar.parsers(comandos) == fixture('parsers.json')


def test_bloques_iguales():
    _, tts = generar.viejo()
    assert generar.bloques(tts) == fixture('bloques.json')


# Los de music ya están en src/: los corre pytest --doctest-modules.
@pytest.mark.parametrize('script', ['narration/tts.py', 'narration/voces.py', 'narration/grabar.py'])
def test_doctests_viejos(script):
    r = doctest.testmod(generar.cargar_script(script))
    assert r.attempted and not r.failed

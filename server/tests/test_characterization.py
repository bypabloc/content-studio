"""El código (server/src/ y lo que queda en server/data/narration/) se comporta igual que las
fixtures de server/tests/fixtures/."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'fixtures'))
import generate  # noqa: E402

FIXTURES = Path(generate.__file__).parent


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding='utf-8'))


def test_parsers_equal_y_livianos(no_heavy):
    commands, _ = generate.current()
    assert generate.parsers(commands) == fixture('parsers.json')


def test_blocks_equal():
    _, tts = generate.current()
    assert generate.blocks(tts) == fixture('bloques.json')

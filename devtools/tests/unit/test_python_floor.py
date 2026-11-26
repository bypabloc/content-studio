"""Tests de devtools/python_floor.py (spec 025, AC-3, D-2): el piso es el mínimo de los pasos python de las recetas."""

import json
from pathlib import Path

from devtools.python_floor import engine_floor


def recipe(folder: Path, name: str, *versions: str) -> None:
    steps = [{'kind': 'python', 'version': v} for v in versions] + [{'kind': 'packages', 'items': []}]
    (folder / f'{name}.json').write_text(json.dumps({'steps': steps}), encoding='utf-8')


def test_ac3_floor_is_min_of_recipes(tmp_path):
    recipe(tmp_path, 'a', '3.12')
    recipe(tmp_path, 'b', '3.10')
    recipe(tmp_path, 'c', '3.11')
    assert engine_floor(tmp_path) == (3, 10)


def test_ac3_floor_rises_when_old_recipe_removed(tmp_path):
    recipe(tmp_path, 'a', '3.12')
    recipe(tmp_path, 'b', '3.11')
    assert engine_floor(tmp_path) == (3, 11)

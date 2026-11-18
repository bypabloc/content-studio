"""Reglas de .claude/rules/codigo-python.md que se pueden comprobar: tope de líneas, sintaxis 3.10 y dependencias."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
MAX_LINEAS = 300


def archivos() -> list[Path]:
    return sorted([RAIZ / 'cli.py', *(RAIZ / 'src').rglob('*.py'), *(RAIZ / 'tests').rglob('*.py')])


ARCHIVOS = archivos()


def nombre(p: Path) -> str:
    return p.relative_to(RAIZ).as_posix()


@pytest.mark.parametrize('ruta', ARCHIVOS, ids=nombre)
def test_tope_de_lineas(ruta):
    lineas = len(ruta.read_text(encoding='utf-8').splitlines())
    assert lineas <= MAX_LINEAS, f'{nombre(ruta)}: {lineas} líneas'


@pytest.mark.parametrize('ruta', ARCHIVOS, ids=nombre)
def test_sintaxis_310(ruta):
    """compile() con el intérprete de la matriz de CI y ast con la gramática de 3.10 (CosyVoice corre en 3.10)."""
    fuente = ruta.read_text(encoding='utf-8')
    compile(fuente, str(ruta), 'exec')
    ast.parse(fuente, str(ruta), feature_version=(3, 10))


def test_codigo_solo_en_src():
    """narration/ y music/ son carpetas de datos; en la raíz solo queda el shim cli.py."""
    sueltos = [*RAIZ.glob('*.py'), *RAIZ.glob('narration/*.py'), *RAIZ.glob('music/*.py')]
    assert [nombre(p) for p in sueltos] == ['cli.py']


def test_dependencias_cli_iguales_a_pyproject():
    deps = r'dependencies = (\[.*?\])'
    cabecera = re.search(deps, (RAIZ / 'cli.py').read_text(encoding='utf-8'))[1]
    proyecto = re.search(deps, (RAIZ / 'pyproject.toml').read_text(encoding='utf-8'))[1]
    assert ast.literal_eval(cabecera) == ast.literal_eval(proyecto)

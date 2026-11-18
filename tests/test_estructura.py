"""Reglas de .claude/rules/codigo-python.md que se pueden comprobar: tope de líneas, sintaxis 3.10 y dependencias."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
MAX_LINEAS = 300
# Temporal: archivos viejos que ya pasaban el tope. Se dividen al migrar a src/ y se sacan de aquí; no pueden crecer.
ALLOWLIST = {
    'cli.py': 489,  # +3 en el paso 4: lee el parser de music desde src/ y lo lanza con -m
    'narration/tts.py': 1294,
    'narration/grabar.py': 482,
    'narration/voces.py': 381,
}


def archivos() -> list[Path]:
    fuera = [p for d in ('src', 'tests') if (RAIZ / d).is_dir() for p in (RAIZ / d).rglob('*.py')]
    return sorted([*RAIZ.glob('*.py'), *RAIZ.glob('narration/*.py'), *RAIZ.glob('music/*.py'), *fuera])


ARCHIVOS = archivos()


def nombre(p: Path) -> str:
    return p.relative_to(RAIZ).as_posix()


@pytest.mark.parametrize('ruta', ARCHIVOS, ids=nombre)
def test_tope_de_lineas(ruta):
    lineas = len(ruta.read_text(encoding='utf-8').splitlines())
    assert lineas <= ALLOWLIST.get(nombre(ruta), MAX_LINEAS), f'{nombre(ruta)}: {lineas} líneas'


@pytest.mark.parametrize('ruta', ARCHIVOS, ids=nombre)
def test_sintaxis_310(ruta):
    """compile() con el intérprete de la matriz de CI y ast con la gramática de 3.10 (CosyVoice corre en 3.10)."""
    fuente = ruta.read_text(encoding='utf-8')
    compile(fuente, str(ruta), 'exec')
    ast.parse(fuente, str(ruta), feature_version=(3, 10))


def test_allowlist_sin_sobrantes():
    """Al dividir un archivo, sale de la ALLOWLIST: así el tope vuelve a regir para él."""
    for clave in ALLOWLIST:
        ruta = RAIZ / clave
        assert ruta.exists() and len(ruta.read_text(encoding='utf-8').splitlines()) > MAX_LINEAS, clave


def test_dependencias_cli_iguales_a_pyproject():
    deps = r'dependencies = (\[.*?\])'
    cabecera = re.search(deps, (RAIZ / 'cli.py').read_text(encoding='utf-8'))[1]
    proyecto = re.search(deps, (RAIZ / 'pyproject.toml').read_text(encoding='utf-8'))[1]
    assert ast.literal_eval(cabecera) == ast.literal_eval(proyecto)

"""Bugs de cli.py. cli.py necesita typer, rich y questionary, así que cada check corre en un python efímero de uv
(las mismas dependencias de su cabecera PEP 723), con el módulo cargado como `cli`."""

import os
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DEPS = ['--with', 'typer>=0.29', '--with', 'rich>=14', '--with', 'questionary>=2.1']


def en_cli(codigo: str) -> None:
    previo = ("import importlib.util, sys; sys.path.insert(0, 'narration'); "
              "s = importlib.util.spec_from_file_location('cli', 'cli.py'); cli = importlib.util.module_from_spec(s); "
              "s.loader.exec_module(cli); tts = cli.cargar('narration/tts.py'); ap = tts.construir_parser()\n")
    r = subprocess.run(['uv', 'run', '-q', '--no-project', *DEPS, 'python', '-c', previo + codigo], cwd=RAIZ,
                       capture_output=True, text=True, encoding='utf-8', env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
    assert r.returncode == 0, r.stdout + r.stderr


def test_ceros_no_se_descartan():
    en_cli("assert cli.a_argv(ap, {'semilla': 0, 'lufs': 0.0}) == ['--semilla', '0', '--lufs', '0.0']\n"
           "assert cli.a_argv(ap, {'semilla': None, 'evaluar': False, 'archivo': []}) == []\n"
           "assert '0' in str(cli.resumen(ap, {'semilla': 0}, 'narration tts').renderable.renderables[0].columns[1]._cells)")



def test_leer_flag_igual_valor_conserva_el_resto():
    en_cli("d, av = cli.leer(tts.construir_parser(), ['--lote=abc', '--modelo', 'qwen-0.6b'])\n"
           "assert d == {'modelo': 'qwen-0.6b'} and '--lote=abc' in av[0], (d, av)\n"
           "d, av = cli.leer(tts.construir_parser(), ['--mod', 'nada', '--semilla', '3'])\n"
           "assert d == {'semilla': 3}, (d, av)")

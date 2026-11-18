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
              "s.loader.exec_module(cli); tts = cli.cargar(cli.COMANDOS['narration tts']); ap = tts.construir_parser()\n")
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    r = subprocess.run(['uv', 'run', '-q', '--no-project', *DEPS, 'python', '-c', previo + codigo], cwd=RAIZ,
                       capture_output=True, text=True, encoding='utf-8', env=env)
    assert r.returncode == 0, r.stdout + r.stderr


def test_ceros_no_se_descartan():
    en_cli("assert cli.a_argv(ap, {'semilla': 0, 'lufs': 0.0}) == ['--semilla', '0', '--lufs', '0.0']\n"
           "assert cli.a_argv(ap, {'semilla': None, 'evaluar': False, 'archivo': []}) == []\n"
           "celdas = cli.resumen(ap, {'semilla': 0}, 'narration tts').renderable.renderables[0].columns[1]._cells\n"
           "assert '0' in str(celdas)")



def test_leer_flag_igual_valor_conserva_el_resto():
    en_cli("d, av = cli.leer(tts.construir_parser(), ['--lote=abc', '--modelo', 'qwen-0.6b'])\n"
           "assert d == {'modelo': 'qwen-0.6b'} and '--lote=abc' in av[0], (d, av)\n"
           "d, av = cli.leer(tts.construir_parser(), ['--mod', 'nada', '--semilla', '3'])\n"
           "assert d == {'semilla': 3}, (d, av)")


def test_rutas_windows_y_comandos():
    en_cli(r"""
import os
assert cli.partir('cli.py') == ['cli.py']
assert cli.partir('') == [] and cli.partir('  ') == []  # ruta opcional vacía: None, no '.'
if os.name == 'nt':
    assert cli.partir(r'D:\g\a.json "C:\con espacio\b.json"') == [r'D:\g\a.json', r'C:\con espacio\b.json']
    assert cli.unir(['--ref', r'C:\a b\x.wav']) == r'--ref "C:\a b\x.wav"'
else:
    assert cli.partir("a.json 'con espacio/b.json'") == ['a.json', 'con espacio/b.json']
    assert cli.unir(['--ref', 'a b.wav']) == "--ref 'a b.wav'"
""")


def test_abreviaturas_y_sys_path():
    en_cli("assert cli.leer(tts.construir_parser(), ['--sem', '3', '--mod=qwen-0.6b']) == "
           "({'semilla': 3, 'modelo': 'qwen-0.6b'}, [])\n"
           "n = len(sys.path); cli.cargar(cli.COMANDOS['narration tts']); assert len(sys.path) == n")

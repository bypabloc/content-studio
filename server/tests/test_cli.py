"""CLI: flags (ceros, --flag=valor, abreviados), rutas de Windows, registro de comandos y el shim cli.py."""

import os
import subprocess
import sys
from pathlib import Path

from content_studio.cli.args import a_argv, leer
from content_studio.cli.commands import REGISTRY, por_key
from content_studio.common.process import join, split
from content_studio.narration.parser import build_parser

ROOT = Path(__file__).resolve().parents[2]
ENV = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}


def cli(*args, python=(sys.executable,)) -> subprocess.CompletedProcess:
    return subprocess.run(
        [*python, 'cli.py', *args],
        cwd=ROOT,
        env=ENV,
        capture_output=True,
        text=True,
        encoding='utf-8',
        stdin=subprocess.DEVNULL,
        timeout=120,
    )


def test_ceros_no_se_descartan():
    from content_studio.cli.flow import summary

    ap = build_parser()
    assert a_argv(ap, {'seed': 0, 'lufs': 0.0}) == ['--seed', '0', '--lufs', '0.0']
    assert a_argv(ap, {'seed': None, 'evaluate': False, 'file': []}) == []
    cells = summary(ap, {'seed': 0}, por_key('narration tts')).renderable.renderables[0].columns[1]._cells
    assert '0' in str(cells)


def test_leer_flag_equal_value_conserva_el_rest():
    d, av = leer(build_parser(), ['--batch=abc', '--model', 'qwen-0.6b'])
    assert d == {'model': 'qwen-0.6b'} and '--batch=abc' in av[0], (d, av)
    d, av = leer(build_parser(), ['--mod', 'nada', '--seed', '3'])
    assert d == {'seed': 3}, (d, av)


def test_abreviaturas():
    assert leer(build_parser(), ['--see', '3', '--mod=qwen-0.6b']) == ({'seed': 3, 'model': 'qwen-0.6b'}, [])


def test_paths_windows_y_commands():
    assert split('cli.py') == ['cli.py']
    assert split('') == [] and split('  ') == []  # ruta opcional vacía: None, no '.'
    if os.name == 'nt':
        assert split(r'D:\g\a.json "C:\con espacio\b.json"') == [r'D:\g\a.json', r'C:\con espacio\b.json']
        assert join(['--ref', r'C:\a b\x.wav']) == r'--ref "C:\a b\x.wav"'
    else:
        assert split("a.json 'con espacio/b.json'") == ['a.json', 'con espacio/b.json']
        assert join(['--ref', 'a b.wav']) == "--ref 'a b.wav'"


def test_registry():
    assert [c.key for c in REGISTRY] == ['narration tts', 'narration grabar', 'narration voces', 'music']
    for cmd in REGISTRY:
        mod = cmd.load()
        dests = {a.dest for a in mod.build_parser()._actions}
        assert set(cmd.catalog(mod)) <= dests, cmd.key  # cada catálogo es de un flag real
    assert {o.value for o in por_key('music').catalog(por_key('music').load())['model']} == {
        'acestep',
        'heartmula',
    }


def test_no_tty_no_question():
    r = cli()
    assert r.returncode == 0 and 'narration' in r.stdout and 'music' in r.stdout, r.stderr
    r = cli('music', '--model', 'acestep', '--style', 'bossa nova')  # inválido: falla en vez de preguntar
    assert r.returncode == 1 and '--key' in r.stderr, r.stdout + r.stderr


def test_ac6_flags_en_ingles():
    """AC-6: el help muestra los flags en inglés y el flag viejo en español ya no existe."""
    for comando in (('narration', 'tts'), ('music',)):
        ayuda = cli(*comando, '--help')
        assert ayuda.returncode == 0 and '--model' in ayuda.stdout and '--modelo' not in ayuda.stdout, ayuda.stdout
    viejo = cli('narration', 'tts', '--modelo', 'qwen-0.6b')
    assert viejo.returncode == 2, viejo.stdout + viejo.stderr


def test_python_no_typer_se_relanza_con_uv():
    """Un python efímero sin dependencias: cli.py se relanza con `uv run --script`."""
    no = ('uv', 'run', '-q', '--isolated', '--no-project', 'python')
    missing = subprocess.run([*no, '-c', 'import typer'], cwd=ROOT, capture_output=True)
    assert missing.returncode != 0
    r = cli('narration', 'tts', '--help', python=no)
    assert r.returncode == 0 and '--model' in r.stdout, r.stdout + r.stderr

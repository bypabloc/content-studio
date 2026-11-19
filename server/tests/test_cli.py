"""CLI: flags (ceros, --flag=valor, abreviados), rutas de Windows, registro de comandos y el shim cli.py."""

import os
import subprocess
import sys
from pathlib import Path

from content_studio.cli.args import a_argv, leer
from content_studio.cli.comandos import REGISTRO, por_clave
from content_studio.comun.proceso import partir, unir
from content_studio.narration.parser import construir_parser

RAIZ = Path(__file__).resolve().parents[2]
ENV = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}


def cli(*args, python=(sys.executable,)) -> subprocess.CompletedProcess:
    return subprocess.run(
        [*python, 'cli.py', *args],
        cwd=RAIZ,
        env=ENV,
        capture_output=True,
        text=True,
        encoding='utf-8',
        stdin=subprocess.DEVNULL,
        timeout=120,
    )


def test_ceros_no_se_descartan():
    from content_studio.cli.flujo import resumen

    ap = construir_parser()
    assert a_argv(ap, {'semilla': 0, 'lufs': 0.0}) == ['--semilla', '0', '--lufs', '0.0']
    assert a_argv(ap, {'semilla': None, 'evaluar': False, 'archivo': []}) == []
    celdas = resumen(ap, {'semilla': 0}, por_clave('narration tts')).renderable.renderables[0].columns[1]._cells
    assert '0' in str(celdas)


def test_leer_flag_igual_valor_conserva_el_resto():
    d, av = leer(construir_parser(), ['--lote=abc', '--modelo', 'qwen-0.6b'])
    assert d == {'modelo': 'qwen-0.6b'} and '--lote=abc' in av[0], (d, av)
    d, av = leer(construir_parser(), ['--mod', 'nada', '--semilla', '3'])
    assert d == {'semilla': 3}, (d, av)


def test_abreviaturas():
    assert leer(construir_parser(), ['--sem', '3', '--mod=qwen-0.6b']) == ({'semilla': 3, 'modelo': 'qwen-0.6b'}, [])


def test_rutas_windows_y_comandos():
    assert partir('cli.py') == ['cli.py']
    assert partir('') == [] and partir('  ') == []  # ruta opcional vacía: None, no '.'
    if os.name == 'nt':
        assert partir(r'D:\g\a.json "C:\con espacio\b.json"') == [r'D:\g\a.json', r'C:\con espacio\b.json']
        assert unir(['--ref', r'C:\a b\x.wav']) == r'--ref "C:\a b\x.wav"'
    else:
        assert partir("a.json 'con espacio/b.json'") == ['a.json', 'con espacio/b.json']
        assert unir(['--ref', 'a b.wav']) == "--ref 'a b.wav'"


def test_registro():
    assert [c.clave for c in REGISTRO] == ['narration tts', 'narration grabar', 'narration voces', 'music']
    for cmd in REGISTRO:
        mod = cmd.cargar()
        dests = {a.dest for a in mod.construir_parser()._actions}
        assert set(cmd.catalogo(mod)) <= dests, cmd.clave  # cada catálogo es de un flag real
    assert {o.valor for o in por_clave('music').catalogo(por_clave('music').cargar())['modelo']} == {
        'acestep',
        'heartmula',
    }


def test_sin_tty_no_pregunta():
    r = cli()
    assert r.returncode == 0 and 'narration' in r.stdout and 'music' in r.stdout, r.stderr
    r = cli('music', '--modelo', 'acestep', '--estilo', 'bossa nova')  # inválido: falla en vez de preguntar
    assert r.returncode == 1 and '--tono' in r.stderr, r.stdout + r.stderr


def test_python_sin_typer_se_relanza_con_uv():
    """Un python efímero sin dependencias: cli.py se relanza con `uv run --script`."""
    sin = ('uv', 'run', '-q', '--isolated', '--no-project', 'python')
    falta = subprocess.run([*sin, '-c', 'import typer'], cwd=RAIZ, capture_output=True)
    assert falta.returncode != 0
    r = cli('narration', 'tts', '--help', python=sin)
    assert r.returncode == 0 and '--modelo' in r.stdout, r.stdout + r.stderr

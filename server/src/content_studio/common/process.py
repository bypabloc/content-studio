"""Procesos y consola: relanzar en el venv de un motor, PYTHONPATH con src/, comandos para mostrar. Solo stdlib."""

from __future__ import annotations

import os
import shlex
import signal
import subprocess
import sys
from pathlib import Path

from content_studio import paths


def relaunch(args: list[str], env: dict[str, str] | None = None) -> None:
    """os.exec*. En Windows no reemplaza el proceso (el padre sale y la terminal vuelve al prompt con el
    hijo corriendo), así que ahí se espera al hijo, que se queda con el Ctrl+C."""
    sys.stdout.flush()
    if os.name == 'nt':
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        sys.exit(subprocess.call(args, env=env))
    if env is None:
        os.execvp(args[0], args)
    os.execvpe(args[0], args, env)


def python_de(venv: Path) -> Path:
    """El python de un venv: Scripts/ en Windows, bin/ en POSIX."""
    return venv / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def env_src(env: dict[str, str] | None = None) -> dict[str, str]:
    """Entorno con src/ antepuesto a PYTHONPATH (os.pathsep: ; en Windows). Así el paquete llega a los venvs de
    los motores sin instalarlo en ellos.

    >>> env_src({'PYTHONPATH': 'x'})['PYTHONPATH'] == os.pathsep.join([str(paths.SRC), 'x'])
    True
    >>> env_src({})['PYTHONPATH'] == str(paths.SRC)
    True
    """
    env = dict(os.environ if env is None else env)
    env['PYTHONPATH'] = os.pathsep.join(p for p in (str(paths.SRC), env.get('PYTHONPATH')) if p)
    return env


def use_venv(venv: Path, readme: str, module: str | None = None, script: str | None = None) -> None:
    """Relanza este proceso con el python de `venv`, si no se está corriendo ya en él: `-m modulo` o `script`,
    con los mismos argumentos. `readme` es el que explica la instalación, para el error si falta el venv."""
    resolved = venv.resolve()
    if resolved.is_relative_to(paths.engines_dir().resolve()):
        os.environ['HF_HOME'] = str(paths.models_cache())
    if Path(sys.prefix).resolve() == resolved:
        return
    py = python_de(venv)
    if not py.exists():
        display = venv.relative_to(paths.ROOT) if venv.is_relative_to(paths.ROOT) else venv
        sys.exit(f'Missing {display.as_posix()}. See the installation in {readme}.')
    relaunch([str(py), *(['-m', module] if module else [script]), *sys.argv[1:]], env_src())


def console_utf8() -> None:
    """cp1252 (Windows, a una tubería) no tiene ≤, – ni los íconos: que se reemplacen en vez de reventar."""
    for f in (sys.stdout, sys.stderr):
        f.reconfigure(errors='replace')


def join(args: list[str]) -> str:
    """Comando para mostrar, con las comillas del shell de este sistema (shlex.join pone comillas posix).

    >>> join(['--ref', 'a b.wav']) == ('--ref "a b.wav"' if os.name == 'nt' else "--ref 'a b.wav'")
    True
    """
    return subprocess.list2cmdline(args) if os.name == 'nt' else shlex.join(args)


def split(text: str) -> list[str]:
    r"""Rutas escritas en una línea. Si el texto entero es una ruta que existe (aunque tenga espacios), es una sola.
    En Windows sin el modo posix, que se come las \ (D:\a.json salía D:a.json), y sin las comillas.

    >>> split('') == split('  ') == []
    True
    >>> split('a.json "con espacio/b.json"')
    ['a.json', 'con espacio/b.json']
    """
    if text.strip() and Path(text.strip()).exists():  # Path('') es '.', que existe
        return [text.strip()]
    if os.name != 'nt':
        return shlex.split(text)
    return [t[1:-1] if len(t) > 1 and t[0] == t[-1] and t[0] in '"\'' else t for t in shlex.split(text, posix=False)]

"""`python -m devtools app-check run`: la app real del worktree, aislada y manejada por CDP (spec 024).

Compila el binario de este commit, lo abre con su propia carpeta de WebView2, base y home bajo `tmp/app-check/<run>/`,
espera su CDP y corre los escenarios de Playwright (`tests/e2e/app-check/<nombre>.check.ts`). No usa el mouse ni el
teclado: Computer Use está prohibido en este repo (computer_use_guard.py). Exit 0 si todo pasa, 1 si falla un
escenario, 2 si fallan la compilación, el arranque o un argumento. stdout: una línea JSON; stderr: el progreso.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from devtools.paths import ROOT
from devtools.worktree import main_checkout

from . import env, launch


def commit(root: Path) -> str:
    """El commit del worktree: el binario se compila desde él."""
    return subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True).stdout.strip()


def user_db(root: Path) -> Path:
    """La base del usuario para `--data=real`: la de `CONTENT_STUDIO_DB` o la del checkout principal."""
    override = os.environ.get('CONTENT_STUDIO_DB')
    return Path(override) if override else main_checkout(root) / 'var' / 'content-studio.db'


def parser() -> argparse.ArgumentParser:
    """Los argumentos de `app-check`."""
    top = argparse.ArgumentParser(prog='python -m devtools app-check', description=__doc__.splitlines()[0])
    sub = top.add_subparsers(dest='command')
    run = sub.add_parser('run', help='build, open and check the app of this worktree')
    run.add_argument('--scenario', action='append', help='tests/e2e/app-check/<name>.check.ts (repeatable)')
    run.add_argument(
        '--data', choices=env.MODES, default='temp', help="temp (default) or the user's real data, read-only"
    )
    return top


def emit(result: dict, code: int) -> int:
    """Imprime la línea JSON y devuelve el exit code."""
    print(json.dumps(result, ensure_ascii=False))
    return code


def run(names: list[str], data: str) -> int:
    """Una corrida completa; los procesos que abre mueren al cerrar el Job."""
    if os.name != 'nt':
        return emit({'error': 'app-check needs Windows and WebView2'}, 2)
    try:
        run_ = env.prepare(ROOT, data, datetime.now(), source_db=user_db(ROOT) if data == 'real' else None)
    except env.AppCheckError as error:
        return emit({'error': str(error)}, 2)
    log = ROOT / 'logs' / f'app-check-{run_.dir.name}.log'
    result: dict = {
        'run': run_.dir.relative_to(ROOT).as_posix(),
        'commit': commit(ROOT),
        'data': data,
        'scenarios': names,
        'log': log.relative_to(ROOT).as_posix(),
    }
    merged = {**os.environ, **run_.env}
    print(f'app-check: building {result["commit"][:7]} ({result["log"]})', file=sys.stderr)
    if launch.build(ROOT, run_.env, log) != 0:
        return emit({**result, 'error': 'build failed: see the log'}, 2)
    exe = launch.binary(run_.env)
    if not exe.is_file():
        return emit({**result, 'error': f'binary not found at {exe}'}, 2)
    result['binary'] = exe.relative_to(ROOT).as_posix() if exe.is_relative_to(ROOT) else str(exe)
    try:
        with launch.Job() as job:
            proc = job.start([str(exe)], merged, log)
            print(f'app-check: waiting for CDP on port {run_.port}', file=sys.stderr)
            if not launch.wait_cdp(run_.port, alive=lambda: proc.poll() is None):
                return emit({**result, 'error': f'CDP did not answer on port {run_.port}: see the log'}, 2)
            code = launch.scenarios(ROOT, run_.port, run_.dir, data, names, log)
    except KeyboardInterrupt:
        print('app-check: interrupted; the run processes were closed', file=sys.stderr)
        return 130
    report = run_.dir / 'report.json'
    if report.is_file():
        result.update(json.loads(report.read_text(encoding='utf-8')))
    return emit(result, 0 if code == 0 else 1)


def main(argv: list[str]) -> int:
    """Entrada del comando: `run [--scenario=<n>]... [--data=temp|real]`."""
    options = parser().parse_args(argv)
    if options.command != 'run':
        parser().print_help(sys.stderr)
        return 2
    return run(options.scenario or ['smoke'], options.data)

"""SessionStart + PostToolBatch: refresca el grafo de graphify cuando quedó viejo.

Nunca bloquea. El disparador es "hay un fuente más nuevo que graph.json" (edits del agente, manuales o git pull).
`graphify update .` es AST puro (sin LLM ni costo) y corre en segundo plano con un lock (mkdir atómico). Con `--run`
es el proceso de fondo: actualiza, toca graph.json y suelta el lock. Funciona igual en Windows y en WSL.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR', Path(__file__).resolve().parents[2]))
GRAPH = ROOT / 'graphify-out' / 'graph.json'
LOCK = ROOT / 'graphify-out' / '.update.lock'
PATTERNS = ['*.py', '*.md']


def is_stale() -> bool:
    """True si algún fuente (versionado o nuevo sin ignorar) es más nuevo que el grafo."""
    listed = subprocess.run(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '--', *PATTERNS],
        cwd=ROOT,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    graph_mtime = GRAPH.stat().st_mtime
    return any((ROOT / rel).is_file() and (ROOT / rel).stat().st_mtime > graph_mtime for rel in listed)


def run() -> None:
    try:
        subprocess.run(['graphify', 'update', '.'], cwd=ROOT, capture_output=True, timeout=300, check=False)
        # Si el contenido no cambió, graphify no reescribe graph.json: el mtime viejo dispararía un rebuild por lote.
        GRAPH.touch()
    finally:
        LOCK.rmdir()


def main() -> None:
    if not GRAPH.exists() or not shutil.which('graphify') or not is_stale():
        return
    try:
        LOCK.mkdir()
    except FileExistsError:
        return
    # ponytail: sin cola; si hay un update en curso, el próximo lote lo reintenta.
    detached = {'creationflags': 0x00000008} if os.name == 'nt' else {'start_new_session': True}  # DETACHED_PROCESS
    subprocess.Popen(
        [sys.executable, __file__, '--run'],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **detached,
    )
    print('[graphify] graph is outdated: rebuilding in the background')


if __name__ == '__main__':
    run() if sys.argv[1:] == ['--run'] else main()

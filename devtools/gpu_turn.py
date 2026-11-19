"""`gpu-turn status|run`: un modelo a la vez en la GPU, también entre sesiones y worktrees (regla turno-gpu.md).

En 8 GB no caben dos modelos: si la VRAM desborda a la RAM compartida de WSL, todo va ~4× más lento. El turno es un
candado en el checkout principal (tmp/gpu-turn/lock.json, compartido por todos los worktrees) que toma
`run -- <comando>` al empezar y suelta al terminar, también con Ctrl+C o un error. `status` dice quién lo tiene, la
VRAM en uso y qué sesiones de Claude Code del proyecto hay que avisar con SendMessage.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from .worktree import main_checkout

STILL_ACTIVE = 259


def lock(main: Path) -> Path:
    return main / 'tmp/gpu-turn/lock.json'


def alive(pid: int, platform: str) -> bool | None:
    """True/False si el proceso vive; None si es de otro sistema (un candado de WSL visto desde Windows)."""
    if platform != sys.platform:
        return None
    if os.name == 'nt':
        import ctypes

        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        k32.GetExitCodeProcess(h, ctypes.byref(code))
        k32.CloseHandle(h)
        return code.value == STILL_ACTIVE
    try:
        os.kill(pid, 0)  # señal 0: solo comprueba (en Windows os.kill mataría el proceso)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def read(main: Path) -> dict | None:
    """Dueño del turno, o None si está libre (sin candado o con el proceso muerto)."""
    try:
        owner = json.loads(lock(main).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if alive(owner.get('pid', 0), owner.get('platform', '')) is False:
        return None
    return owner


def take(main: Path, job: str, command: list[str]) -> dict | None:
    """Toma el turno (creación atómica); devuelve el dueño actual si está ocupado, o None si lo tomó."""
    lock_file = lock(main)
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    owner = read(main)
    if owner:
        return owner
    lock_file.unlink(missing_ok=True)  # candado huérfano: su proceso murió
    data = {'pid': os.getpid(), 'platform': sys.platform, 'work': job, 'command': ' '.join(command)}
    data['since'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    try:
        with lock_file.open('x', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except FileExistsError:
        return read(main) or {'work': '?', 'command': 'another process took the turn at the same time'}
    return None


def release(main: Path) -> None:
    lock_file = lock(main)
    try:
        if json.loads(lock_file.read_text(encoding='utf-8')).get('pid') == os.getpid():
            lock_file.unlink()
    except (OSError, ValueError):
        return


def vram() -> str | None:
    """`usada/total MiB` de la GPU 0, o None sin nvidia-smi."""
    if not shutil.which('nvidia-smi'):
        return None
    q = ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits']
    r = subprocess.run(q, capture_output=True, text=True, check=False)
    parts = [p.strip() for p in r.stdout.splitlines()[0].split(',')] if r.returncode == 0 and r.stdout else []
    return f'{parts[0]}/{parts[1]} MiB' if len(parts) == 2 else None


def sessions(main: Path) -> list[dict]:
    """Sesiones de Claude Code abiertas en el proyecto (principal o ../<repo>-worktrees/), por su `cwd`."""
    base = Path(os.environ.get('CLAUDE_CONFIG_DIR') or Path.home() / '.claude') / 'sessions'
    roots = [str(main).lower(), str(main.parent / f'{main.name}-worktrees').lower()]
    out = []
    for f in sorted(base.glob('*.json')) if base.is_dir() else []:
        try:
            s = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        cwd = str(s.get('cwd', '')).replace('/', os.sep).lower()
        if any(cwd == r or cwd.startswith(r + os.sep) for r in roots) and alive(s.get('pid', 0), sys.platform):
            out.append({'pid': s.get('pid'), 'name': s.get('name'), 'cwd': s.get('cwd')})
    return out


def status(main: Path) -> int:
    owner = read(main)
    data = {'state': 'busy' if owner else 'free', 'holder': owner, 'vram': vram(), 'sessions': sessions(main)}
    print(json.dumps(data, ensure_ascii=False))
    if owner:
        print(f'busy: {owner.get("work")} · {owner.get("command")} · since {owner.get("since")}', file=sys.stderr)
    else:
        print(f'libre (VRAM {data["vram"] or "?"})', file=sys.stderr)
    return 1 if owner else 0


def run(main: Path, job: str, command: list[str]) -> int:
    owner = take(main, job, command)
    if owner:
        print(
            f'gpu-turn: busy with {owner.get("work")} ({owner.get("command")}); wait for its "gpu free"',
            file=sys.stderr,
        )
        return 1
    try:
        return subprocess.call(command)
    except KeyboardInterrupt:
        return 130
    finally:
        release(main)


def main(argv: list[str]) -> int:
    uso = 'usage: gpu-turn status | gpu-turn run --job=<j> -- <command ...>'
    if not argv or argv[0] in ('-h', '--help'):
        print(uso, file=sys.stderr)
        return 0
    main_root = main_checkout(Path.cwd())
    if argv == ['status']:
        return status(main_root)
    if argv[0] == 'run' and '--' in argv:
        cut = argv.index('--')
        job = next((a.split('=', 1)[1] for a in argv[1:cut] if a.startswith('--job=')), '')
        if job and argv[cut + 1 :]:
            return run(main_root, job, argv[cut + 1 :])
    print(uso, file=sys.stderr)
    return 2

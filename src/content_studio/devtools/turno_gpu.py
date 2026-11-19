"""`turno-gpu status|run`: un modelo a la vez en la GPU, también entre sesiones y worktrees (regla turno-gpu.md).

En 8 GB no caben dos modelos: si la VRAM desborda a la RAM compartida de WSL, todo va ~4× más lento. El turno es un
candado en el checkout principal (tmp/turno-gpu/lock.json, compartido por todos los worktrees) que toma
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

from content_studio.devtools.worktree import principal

STILL_ACTIVE = 259


def candado(main: Path) -> Path:
    return main / 'tmp/turno-gpu/lock.json'


def vivo(pid: int, plataforma: str) -> bool | None:
    """True/False si el proceso vive; None si es de otro sistema (un candado de WSL visto desde Windows)."""
    if plataforma != sys.platform:
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


def leer(main: Path) -> dict | None:
    """Dueño del turno, o None si está libre (sin candado o con el proceso muerto)."""
    try:
        dueño = json.loads(candado(main).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if vivo(dueño.get('pid', 0), dueño.get('platform', '')) is False:
        return None
    return dueño


def tomar(main: Path, trabajo: str, comando: list[str]) -> dict | None:
    """Toma el turno (creación atómica); devuelve el dueño actual si está ocupado, o None si lo tomó."""
    lock = candado(main)
    lock.parent.mkdir(parents=True, exist_ok=True)
    dueño = leer(main)
    if dueño:
        return dueño
    lock.unlink(missing_ok=True)  # candado huérfano: su proceso murió
    datos = {'pid': os.getpid(), 'platform': sys.platform, 'work': trabajo, 'command': ' '.join(comando)}
    datos['since'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    try:
        with lock.open('x', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False)
    except FileExistsError:
        return leer(main) or {'work': '?', 'command': 'otro proceso tomó el turno a la vez'}
    return None


def soltar(main: Path) -> None:
    lock = candado(main)
    try:
        if json.loads(lock.read_text(encoding='utf-8')).get('pid') == os.getpid():
            lock.unlink()
    except (OSError, ValueError):
        return


def vram() -> str | None:
    """`usada/total MiB` de la GPU 0, o None sin nvidia-smi."""
    if not shutil.which('nvidia-smi'):
        return None
    q = ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits']
    r = subprocess.run(q, capture_output=True, text=True, check=False)
    partes = [p.strip() for p in r.stdout.splitlines()[0].split(',')] if r.returncode == 0 and r.stdout else []
    return f'{partes[0]}/{partes[1]} MiB' if len(partes) == 2 else None


def sesiones(main: Path) -> list[dict]:
    """Sesiones de Claude Code abiertas en el proyecto (principal o ../<repo>-worktrees/), por su `cwd`."""
    base = Path(os.environ.get('CLAUDE_CONFIG_DIR') or Path.home() / '.claude') / 'sessions'
    raices = [str(main).lower(), str(main.parent / f'{main.name}-worktrees').lower()]
    out = []
    for f in sorted(base.glob('*.json')) if base.is_dir() else []:
        try:
            s = json.loads(f.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        cwd = str(s.get('cwd', '')).replace('/', os.sep).lower()
        if any(cwd == r or cwd.startswith(r + os.sep) for r in raices) and vivo(s.get('pid', 0), sys.platform):
            out.append({'pid': s.get('pid'), 'name': s.get('name'), 'cwd': s.get('cwd')})
    return out


def status(main: Path) -> int:
    dueño = leer(main)
    datos = {'state': 'busy' if dueño else 'free', 'holder': dueño, 'vram': vram(), 'sessions': sesiones(main)}
    print(json.dumps(datos, ensure_ascii=False))
    if dueño:
        print(f'ocupada: {dueño.get("work")} · {dueño.get("command")} · desde {dueño.get("since")}', file=sys.stderr)
    else:
        print(f'libre (VRAM {datos["vram"] or "?"})', file=sys.stderr)
    return 1 if dueño else 0


def run(main: Path, trabajo: str, comando: list[str]) -> int:
    dueño = tomar(main, trabajo, comando)
    if dueño:
        print(
            f'turno-gpu: ocupada por {dueño.get("work")} ({dueño.get("command")}); espera su «gpu libre»',
            file=sys.stderr,
        )
        return 1
    try:
        return subprocess.call(comando)
    except KeyboardInterrupt:
        return 130
    finally:
        soltar(main)


def main(argv: list[str]) -> int:
    uso = 'uso: turno-gpu status | turno-gpu run --trabajo=<t> -- <comando ...>'
    if not argv or argv[0] in ('-h', '--help'):
        print(uso, file=sys.stderr)
        return 0
    main_root = principal(Path.cwd())
    if argv == ['status']:
        return status(main_root)
    if argv[0] == 'run' and '--' in argv:
        corte = argv.index('--')
        trabajo = next((a.split('=', 1)[1] for a in argv[1:corte] if a.startswith('--trabajo=')), '')
        if trabajo and argv[corte + 1 :]:
            return run(main_root, trabajo, argv[corte + 1 :])
    print(uso, file=sys.stderr)
    return 2

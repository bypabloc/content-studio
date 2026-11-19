"""Bitácora del handoff: qué inyectó cada hook, qué hizo el mod y cuándo se bloqueó un Stop.

Cada evento es una línea JSON en tmp/handoff/.log/events.jsonl. Con `work`, guarda además un snapshot de PROGRESS,
DECISIONS y NOTES junto al mensaje inyectado en .log/snapshots/<trabajo>/<sha>.json (dos inyecciones iguales comparten
archivo). Nunca falla: un error de disco no puede tumbar el hook.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

FILES = ('PROGRESS.md', 'DECISIONS.md', 'NOTES.md')


def _read(path: Path) -> str | None:
    return path.read_text(encoding='utf-8', errors='replace') if path.is_file() else None


def _snapshot(log: Path, folder: Path, work: str, message: str | None) -> str:
    content = {'files': {name: _read(folder / name) for name in FILES}, 'message': message}
    raw = json.dumps(content, ensure_ascii=False, indent=1)
    relative = f'snapshots/{work}/{hashlib.sha256(raw.encode()).hexdigest()[:16]}.json'
    target = log / relative
    if not target.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(raw, encoding='utf-8')
    return relative


def log_event(store: Path, event: dict, work: str | None = None, message: str | None = None) -> None:
    """Agrega `event` a events.jsonl y, con `work`, el snapshot del handoff de ese trabajo."""
    # ponytail: sin rotación; tmp/ lo limpia el usuario. Rotar si events.jsonl pasa de decenas de MB.
    log = store / 'tmp/handoff/.log'
    try:
        log.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
        line = {'ts': stamp, **event}
        if work:
            line['work'] = work
            line['snapshot'] = _snapshot(log, store / 'tmp/handoff' / work, work, message)
        with (log / 'events.jsonl').open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(line, ensure_ascii=False) + '\n')
    except OSError:
        return

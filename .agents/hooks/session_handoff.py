"""Handoff en disco por trabajo: lo reinyecta al iniciar, reanudar o compactar, y no deja parar con trabajo pendiente.

Cada trabajo vive en tmp/handoff/<trabajo>/ (PROGRESS, DECISIONS y NOTES) del checkout principal y cada sesión se
vincula a uno con tmp/handoff/.sessions/<session_id>. Un solo script para todos los eventos:

* SessionStart (Claude Code y Codex) y PreInvocation (Antigravity): mensaje con el trabajo vinculado, o el id de la
  sesión y la lista de trabajos activos si no hay vínculo.
* PreCompact: instrucciones para el resumen. Stop: bloquea el cierre del turno mientras haya `Next step` pendiente.
* PreToolUse de AskUserQuestion: con una spec en ejecución, solo se pregunta por un bloqueo de BLOCK_REASONS.
* PostToolUse de Write/Edit sobre un PROGRESS.md: nombra las líneas de estado largas.
* `--status`: JSON de las líneas de estado para el mod handoff-compact. `--log`: agrega la entrada a la bitácora.

Regla: .agents/rules/session-handoff.md. Adaptado de klinikae (sin la pausa larga de Codex ni OpenCode).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

import handoff_text as T
from handoff_log import log_event
from handoff_store import SAFE_NAME, active_works, current_work, main_checkout, spec_folder, status_of
from handoff_store import git as _git
from handoff_store import handoff_dir as _handoff
from handoff_store import read_progress as _progress
from handoff_text import CONTINUE, missing, progress_fields

__all__ = ['active_works', 'current_work', 'main_checkout', 'spec_folder', 'status_of']
FILES = ('PROGRESS.md', 'DECISIONS.md', 'NOTES.md')
LIMIT = 6000
PROGRESS_PATH = re.compile(r'(?:^|/)tmp/handoff/[^/]+/PROGRESS\.md$')
MAX_BLOCKS = 3


def precompact_message(store: Path, session_id: str, branch: str) -> str:
    """Instrucciones para el resumen de compactación; vacío sin trabajo."""
    work = current_work(store, session_id, branch)
    if not work:
        return ''
    folder = _handoff(store) / work
    fields = progress_fields(_progress(folder))
    lines = [T.PRECOMPACT.format(work=work, folder=folder)]
    if fields.get('next_step'):
        lines.append(T.PRECOMPACT_STEP.format(step=fields['next_step'][:160]))
    if fields.get('status') not in ('done', 'blocked'):
        lines.append(CONTINUE)
    return '\n'.join(lines)


def stop_reply(store: Path, session_id: str, branch: str) -> str:
    """Stop: bloquea el cierre del turno mientras el trabajo vinculado siga pendiente; vacío = dejar parar.

    Pendiente = `Next step:` sin `Status: done|blocked` y fuera de `external-wait`. Tras MAX_BLOCKS bloqueos seguidos
    sin que PROGRESS.md cambie, deja parar (anti-bucle).
    """
    work = current_work(store, session_id, branch)
    if not work or not SAFE_NAME.match(session_id or ''):
        return ''
    text = _progress(_handoff(store) / work)
    fields = progress_fields(text)
    decide = fields.get('status') == 'blocked' and not T.blocked_for_user(fields)
    release = (
        None
        if decide
        else (
            (fields.get('status') if fields.get('status') in ('done', 'blocked') else None)
            or ('no-step' if 'next_step' not in fields else None)
            or ('external-wait' if fields.get('phase') == 'external-wait' else None)
        )
    )
    if release:
        log_event(store, {'event': 'stop.release', 'session': session_id, 'reason': release})
        return ''
    digest = hashlib.sha256(text.encode()).hexdigest()
    state = _handoff(store) / '.stop' / session_id
    try:
        previous = json.loads(state.read_text(encoding='utf-8')) if state.is_file() else {}
    except json.JSONDecodeError:
        previous = {}
    blocks = previous.get('blocks', 0) + 1 if previous.get('hash') == digest else 1
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps({'hash': digest, 'blocks': blocks}), encoding='utf-8')
    if blocks > MAX_BLOCKS:
        log_event(store, {'event': 'stop.release', 'session': session_id, 'reason': 'cap', 'blocks': blocks}, work)
        return ''
    if decide:
        # cspell:ignore motivo: prosa del agente en español (D-1)
        reason = f'[session-handoff] {T.DECIDE.format(reason=fields.get("reason", "sin motivo"))}'
    else:
        reason = T.STOP[blocks - 1].format(work=work, step=fields['next_step'][:160], blocks=blocks, cap=MAX_BLOCKS)
    log_event(store, {'event': 'stop.block', 'session': session_id, 'blocks': blocks}, work)
    return json.dumps({'decision': 'block', 'reason': reason}, ensure_ascii=False)


def ask_reply(root: Path, store: Path, session_id: str, branch: str) -> str:
    """AskUserQuestion con una spec en ejecución: solo con un bloqueo de BLOCK_REASONS. Vacío = permitir."""
    work = current_work(store, session_id, branch)
    if not work or not (spec_folder(root, work) or spec_folder(root, branch)):
        return ''
    if T.blocked_for_user(progress_fields(_progress(_handoff(store) / work))):
        return ''
    log_event(store, {'event': 'ask.deny', 'session': session_id}, work)
    decision = {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny', 'permissionDecisionReason': T.ASK_DENIED}
    return json.dumps({'hookSpecificOutput': decision}, ensure_ascii=False)


def progress_reply(payload: dict) -> str:
    """Write/Edit de un PROGRESS.md del handoff: nombra en el acto las líneas de estado largas. Vacío = nada."""
    path = Path(str(payload.get('tool_input', {}).get('file_path', '')))
    if not PROGRESS_PATH.search(path.as_posix()) or not path.is_file():
        return ''
    long = T.too_long(progress_fields(path.read_text(encoding='utf-8', errors='replace')))
    if not long:
        return ''
    reason = f'[session-handoff] {T.LONG.format(max=T.LINE_MAX, labels=", ".join(long))}'
    return json.dumps({'decision': 'block', 'reason': reason}, ensure_ascii=False)


def _excerpt(path: Path) -> str:
    text = path.read_text(encoding='utf-8', errors='replace').strip()
    return text if len(text) <= LIMIT else text[:LIMIT] + T.TRUNCATED.format(more=len(text) - LIMIT, name=path.name)


def _bound_message(root: Path, store: Path, work: str, branch: str, source: str) -> list[str]:
    """Mensaje de un trabajo vinculado según el evento de origen, el estado y la fase."""
    folder = _handoff(store) / work
    fields = progress_fields(_progress(folder))
    lines = [
        T.HEADER.format(work=work, folder=folder, branch=branch or '(detached)'),
        T.SOURCE_TEXT.get(source, T.REREAD),
    ]
    if fields.get('status') == 'done':
        lines.append(T.DONE.format(folder=folder))
        return lines
    if fields.get('status') == 'blocked':
        text = T.BLOCKED if T.blocked_for_user(fields) else T.DECIDE
        lines.append(text.format(reason=fields.get('reason', '(sin motivo)')))
    else:
        lines.append(CONTINUE)
        if fields.get('phase'):
            lines.append(T.PHASE_TEXT[fields['phase']])
    lines.append(T.GPU)
    gaps = missing(fields)
    if gaps:
        lines.append(T.FORMAT.format(missing=', '.join(gaps)))
    long = T.too_long(fields)
    if long:
        lines.append(T.LONG.format(max=T.LINE_MAX, labels=', '.join(long)))
    spec = spec_folder(root, work) or spec_folder(root, branch)
    if spec:
        lines.append(T.SPEC.format(spec=spec))
    lines.append(T.SAVED)
    for name in FILES:
        path = folder / name
        lines.append(f'--- {name} ---\n{_excerpt(path)}' if path.is_file() else T.MISSING_FILE.format(name=name))
    return lines


def build_message(root: Path, branch: str, source: str, session_id: str, store: Path | None = None) -> str:
    """Texto a inyectar; vacío si no hay trabajo ni id de sesión. `store` es el checkout principal (tmp/handoff/)."""
    store = store or root
    work = current_work(store, session_id, branch)
    if work:
        return '\n'.join(_bound_message(root, store, work, branch, source))
    if not session_id:
        return ''
    lines = [T.UNBOUND.format(session=session_id, base=_handoff(store)), T.GPU]
    if source == 'compact':
        lines.append(T.SUMMARIZED)
    works = active_works(store)
    if works:
        lines.append(T.ACTIVE)
        lines.extend(f'- {name}: {step}' if step else f'- {name}' for name, step in works)
    return '\n'.join(lines)


def read_event(payload: dict) -> tuple[str, str, str, str]:
    """(session_id, cwd, source, formato de salida). Antigravity manda camelCase en PreInvocation."""
    if 'conversationId' in payload:
        paths = payload.get('workspacePaths') or ['']
        return str(payload['conversationId']), str(paths[0]), 'invocation', 'antigravity'
    if payload.get('hook_event_name') == 'PreCompact':
        return str(payload.get('session_id') or ''), str(payload.get('cwd') or ''), 'precompact', 'precompact'
    source = str(payload.get('source') or 'compact')
    return str(payload.get('session_id') or ''), str(payload.get('cwd') or ''), source, 'session-start'


def render(message: str, output: str = 'session-start') -> str:
    """Salida JSON del hook: `additionalContext` (Claude Code y Codex) o `ephemeralMessage` (Antigravity)."""
    if output == 'antigravity':
        return json.dumps({'injectSteps': [{'ephemeralMessage': message}]}, ensure_ascii=False)
    context = {'hookEventName': 'SessionStart', 'additionalContext': message}
    return json.dumps({'hookSpecificOutput': context}, ensure_ascii=False)


def _agent(output: str) -> str:
    if output == 'antigravity':
        return 'antigravity'
    return 'claude' if os.environ.get('CLAUDE_PROJECT_DIR') else 'codex'


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read() or '{}')
    except json.JSONDecodeError:
        payload = {}
    session_id, cwd_text, source, output = read_event(payload)
    cwd = Path(cwd_text or Path.cwd())
    root = Path(_git(cwd, 'rev-parse', '--show-toplevel') or cwd)
    store = main_checkout(cwd) or root
    if '--log' in sys.argv[1:]:
        log_event(store, {k: v for k, v in payload.items() if k != 'cwd'})
        return
    branch = _git(root, 'branch', '--show-current')
    event = payload.get('hook_event_name')
    reply = ''
    if '--status' in sys.argv[1:]:
        reply = json.dumps(status_of(store, session_id, branch), ensure_ascii=False)
    elif event == 'PostToolUse':
        reply = progress_reply(payload)
    elif event == 'PreToolUse':
        reply = ask_reply(root, store, session_id, branch)
    elif event == 'Stop':
        reply = stop_reply(store, session_id, branch)
    elif output == 'precompact':
        reply = precompact_message(store, session_id, branch)
        log_event(store, {'event': 'precompact', 'agent': 'claude', 'session': session_id}, None)
    else:
        message = build_message(root, branch, source, session_id, store)
        if not payload.get('probe'):
            base = {'event': 'inject', 'agent': _agent(output), 'session': session_id, 'source': source}
            log_event(store, {**base, 'chars': len(message)}, current_work(store, session_id, branch), message)
        reply = render(message, output) if message else ('{}' if output == 'antigravity' else '')
    if reply:
        print(reply)


if __name__ == '__main__':
    main()

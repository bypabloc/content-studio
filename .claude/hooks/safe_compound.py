"""PreToolUse (Bash): auto-aprueba los comandos compuestos cuyas partes ya están permitidas.

Claude Code pide confirmación ante `$(...)`, comillas invertidas, `&&` o tuberías aunque cada parte tenga su regla
`Bash(...)` en `permissions.allow`. Este hook parte el comando (respetando comillas), evalúa cada sub-comando y el
contenido de cada sustitución contra las reglas, y solo lo aprueba si TODO coincide con `allow`, nada con `deny`/`ask`,
y toda redirección de escritura va a tmp/, logs/ u out/. Ante lo que no entiende (heredoc, subshell, `$((`, comillas
sin cerrar) no responde: el harness pregunta como siempre. Adaptado de klinikae.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import shlex
import sys
from collections.abc import Callable
from pathlib import Path

PH = '__SUBST__'
OPERATOR_CHARS = ';&|<>()\n'
SEPARATOR_CHARS = set(';&|\n')
REDIRECTS = {'>', '>>', '>|', '&>', '&>>', '>&', '<', '<&'}
ASSIGNMENT_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_]*=')
SAFE_DIRS = ('tmp/', 'logs/', 'out/')
Extra = Callable[[list[str]], bool] | None


def _quote_end(s: str, i: int, quote: str) -> int:
    """Índice de la comilla `quote` que cierra; ValueError si no cierra."""
    return s.index(quote, i)


def _dq_end(s: str, i: int) -> int:
    """Índice de la `"` que cierra una cadena doble que empieza en i."""
    while i < len(s):
        c = s[i]
        if c == '\\':
            i += 2
        elif c == '"':
            return i
        elif s.startswith('$(', i):
            i = _paren_end(s, i + 2) + 1
        elif c == '`':
            i = _quote_end(s, i + 1, '`') + 1
        else:
            i += 1
    raise ValueError('comilla doble sin cerrar')


def _paren_end(s: str, i: int) -> int:
    """Índice del `)` que cierra un `$(` cuyo contenido empieza en i."""
    depth = 0
    while i < len(s):
        c = s[i]
        if c == '\\':
            i += 2
            continue
        if c == "'":
            i = _quote_end(s, i + 1, "'") + 1
            continue
        if c == '"':
            i = _dq_end(s, i + 1) + 1
            continue
        if c == '`':
            i = _quote_end(s, i + 1, '`') + 1
            continue
        if s.startswith('$(', i):
            i = _paren_end(s, i + 2) + 1
            continue
        if c == '(':
            depth += 1
        elif c == ')':
            if depth == 0:
                return i
            depth -= 1
        i += 1
    raise ValueError('sustitución sin cerrar')


def _extract(s: str) -> tuple[str, list[str]]:
    """Reemplaza cada `$(...)`/`...` de primer nivel por PH y devuelve su contenido."""
    out: list[str] = []
    inners: list[str] = []
    in_dq = False
    i = 0
    while i < len(s):
        c = s[i]
        if c == '\\':
            out.append(s[i : i + 2])
            i += 2
        elif c == "'" and not in_dq:
            j = _quote_end(s, i + 1, "'")
            out.append(s[i : j + 1])
            i = j + 1
        elif c == '"':
            in_dq = not in_dq
            out.append(c)
            i += 1
        elif s.startswith('$((', i):
            raise ValueError('aritmética no soportada')
        elif s.startswith('$(', i) or c == '`':
            j = _paren_end(s, i + 2) if c == '$' else _quote_end(s, i + 1, '`')
            inners.append(s[i + 2 : j] if c == '$' else s[i + 1 : j])
            out.append(PH)
            i = j + 1
        else:
            out.append(c)
            i += 1
    if in_dq:
        raise ValueError('comilla doble sin cerrar')
    return ''.join(out), inners


def _tokens(s: str) -> list[str]:
    lexer = shlex.shlex(s, posix=True, punctuation_chars=OPERATOR_CHARS)
    lexer.whitespace = ' \t\r'
    lexer.whitespace_split = True
    return list(lexer)


def _rule_matches(rule: str, cmd: str) -> bool:
    if rule.endswith(':*'):
        prefix = rule[:-2]
        return cmd == prefix or cmd.startswith(prefix + ' ')
    if '*' in rule:
        return fnmatch.fnmatchcase(cmd, rule)
    return cmd == rule


def _segment_ok(seg: list[str], allow: list[str], deny: list[str], extra: Extra) -> bool:
    name = next((t for t in seg if not ASSIGNMENT_RE.match(t)), None)
    if name is None:
        return True
    if PH in name:
        return False
    cmd = ' '.join(seg)
    if any(_rule_matches(r, cmd) for r in deny):
        return False
    if any(_rule_matches(r, cmd) for r in allow):
        return True
    return extra is not None and extra(seg)


def is_allowed(
    command: str, allow: list[str], deny: list[str], safe_target: Callable[[str], bool], extra: Extra = None
) -> bool:
    """True si cada parte del comando (y de sus sustituciones) está permitida.

    >>> ok = lambda c: is_allowed(c, ['git log:*', 'uv run pytest:*', 'echo:*'], ['git push:*'], safe_target)
    >>> ok('uv run pytest -q > tmp/u.log 2>&1 && git log --oneline -1'), ok('echo $(git log -1)')
    (True, True)
    >>> ok('git log && git push'), ok('echo x > src/a.py'), ok('rm -rf out')
    (False, False, False)
    """
    try:
        outer, inners = _extract(command)
        tokens = _tokens(outer)
    except ValueError:
        return False
    if not all(is_allowed(i, allow, deny, safe_target, extra) for i in inners):
        return False
    seg: list[str] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok and set(tok) <= set(OPERATOR_CHARS):
            if tok in REDIRECTS:
                if seg and seg[-1].isdigit():
                    seg.pop()
                if i + 1 >= len(tokens):
                    return False
                target = tokens[i + 1]
                dup = tok.endswith('&') and (target.isdigit() or target == '-')
                escribe = not (dup or tok.startswith('<') or target == '/dev/null')
                if escribe and (PH in target or not safe_target(target)):
                    return False
                i += 2
                continue
            if not set(tok) <= SEPARATOR_CHARS:
                return False
            if seg and not _segment_ok(seg, allow, deny, extra):
                return False
            seg = []
        else:
            seg.append(tok)
        i += 1
    return not seg or _segment_ok(seg, allow, deny, extra)


def safe_target(path: str) -> bool:
    """Redirección de escritura permitida: relativa, sin `..`, dentro de tmp/, logs/ u out/."""
    p = path.replace('\\', '/').removeprefix('./')
    return p.startswith(SAFE_DIRS) and '..' not in p.split('/')


def load_rules(project_dir: str) -> tuple[list[str], list[str]]:
    """Reglas Bash de allow y de deny+ask del usuario y del proyecto."""
    home = Path(os.environ.get('CLAUDE_CONFIG_DIR') or Path.home() / '.claude')
    files = [home / 'settings.json', home / 'settings.local.json']
    files += [Path(project_dir) / '.claude' / n for n in ('settings.json', 'settings.local.json')]
    allow: list[str] = []
    block: list[str] = []
    for f in files:
        try:
            perms = json.loads(f.read_text(encoding='utf-8')).get('permissions', {})
        except (OSError, ValueError):
            continue
        for key, bucket in (('allow', allow), ('deny', block), ('ask', block)):
            bucket.extend(r[5:-1] for r in perms.get(key, []) if r.startswith('Bash(') and r.endswith(')'))
    return allow, block


def main() -> None:
    try:
        command = json.load(sys.stdin).get('tool_input', {}).get('command', '')
    except Exception:
        return
    # Un comando simple lo resuelve el harness; solo intervenimos en los compuestos.
    if not command or not any(ch in command for ch in ';&|$`\n>'):
        return
    allow, block = load_rules(os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd()))
    if is_allowed(command, allow, block, safe_target):
        decision = {'hookEventName': 'PreToolUse', 'permissionDecision': 'allow', 'permissionDecisionReason': 'safe'}
        print(json.dumps({'hookSpecificOutput': decision}))


if __name__ == '__main__':
    main()

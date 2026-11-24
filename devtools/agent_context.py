"""`agent-context`: mide las instrucciones que carga cada agente y sale con 1 si alguna pasa su límite.

Lo corre el pre-commit cuando hay archivos de instrucciones staged. Claude Code carga AGENTS.md/CLAUDE.md y las
reglas de .claude/rules/ sin `paths:` en cada sesión; Codex lee AGENTS.md hasta `project_doc_max_bytes`; Antigravity
trunca cada regla de .agents/rules/ y descarta sin avisar la que no tiene un `trigger` válido. Adaptado de klinikae.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from . import paths

LIMITS = {
    'rule': 15_000,  # characters per rule or repo instruction (project decision)
    'claude-always': 80_000,  # characters Claude Code always loads from the repo
    'codex': 32_768,  # bytes de AGENTS.md (project_doc_max_bytes por defecto)
    'agy-rule': 24_000,  # bytes per Antigravity rule
}
TRIGGERS = {'always_on', 'model_decision', 'glob', 'manual'}


def frontmatter(text: str) -> str:
    """Bloque YAML del inicio, sin las rayas; vacío si no hay.

    >>> frontmatter('---\\npaths:\\n  - a\\n---\\n# X'), frontmatter('# X')
    ('paths:\\n  - a', '')
    """
    m = re.match(r'---\n(.*?)\n---\n', text, re.DOTALL)
    return m.group(1) if m else ''


def measure(root: Path) -> tuple[dict, list[str]]:
    """Tamaños por agente y la lista de fallos."""
    failures: list[str] = []
    claude = [root / n for n in ('AGENTS.md', 'CLAUDE.md', 'CLAUDE.local.md') if (root / n).is_file()]
    rules_claude = sorted((root / '.claude/rules').glob('**/*.md'))
    always = claude + [r for r in rules_claude if 'paths:' not in frontmatter(r.read_text(encoding='utf-8'))]
    rules_agy = sorted((root / '.agents/rules').glob('*.md'))
    for f in claude + rules_claude + rules_agy:
        n = len(f.read_text(encoding='utf-8'))
        if n > LIMITS['rule']:
            failures.append(f'{f.relative_to(root).as_posix()}: {n} characters > {LIMITS["rule"]} (details in docs)')
    total = sum(len(f.read_text(encoding='utf-8')) for f in always)
    if total > LIMITS['claude-always']:
        failures.append(f'Claude Code always loads {total} characters > {LIMITS["claude-always"]}')
    agents = root / 'AGENTS.md'
    codex = agents.stat().st_size if agents.is_file() else 0
    if codex > LIMITS['codex']:
        failures.append(f'AGENTS.md: {codex} bytes > {LIMITS["codex"]} (Codex deja de leer)')
    for r in rules_agy:
        data = r.read_bytes()
        # Los bytes cuentan para el límite; el texto se normaliza (en Windows, git hace checkout con CRLF).
        text = data.decode('utf-8').replace('\r\n', '\n')
        trigger = re.search(r'^trigger:\s*(\S+)', frontmatter(text), re.MULTILINE)
        if not trigger or trigger.group(1) not in TRIGGERS:
            failures.append(f'{r.relative_to(root).as_posix()}: with no valid trigger ({", ".join(sorted(TRIGGERS))})')
        if len(data) > LIMITS['agy-rule']:
            failures.append(f'{r.relative_to(root).as_posix()}: {len(data)} bytes > {LIMITS["agy-rule"]}')
    agents = {
        'claude': {'files': len(always), 'chars': total},
        'codex': {'files': int(codex > 0), 'bytes': codex},
        'antigravity': {'files': len(rules_agy), 'bytes': sum(r.stat().st_size for r in rules_agy)},
    }
    return agents, failures


def main(argv: list[str]) -> int:
    """Entrada de `python -m devtools agent-context`: exit 1 si algo pasa su límite."""
    if argv:
        print('usage: agent-context (no arguments)', file=sys.stderr)
        return 0 if argv[0] in ('-h', '--help') else 2
    agents, failures = measure(paths.ROOT)
    print(json.dumps({'agents': agents, 'failures': failures}, ensure_ascii=False))
    for name, data in agents.items():
        print(f'{name}: {data}', file=sys.stderr)
    for f in failures:
        print(f'FALLA {f}', file=sys.stderr)
    return 1 if failures else 0

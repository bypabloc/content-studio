"""`rules [--sync]`: las reglas y skills de .agents/ (fuente) y .claude/ (copia) tienen el mismo cuerpo.

Cada regla vive en `.agents/rules/<r>.md` con el frontmatter de Antigravity (`trigger`, `description`) y en
`.claude/rules/<r>.md` con el de Claude Code (`paths:` opcional; sin él, la regla carga siempre). Cada skill, igual en
`.agents/skills/<s>/SKILL.md` y `.claude/skills/<s>/SKILL.md`. Sin argumentos lista las diferencias (exit 1 si hay);
`--sync` reescribe las copias de .claude/ desde .agents/ conservando su frontmatter.
Regla: agent-config-testing.md.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from . import paths

ONLY_CLAUDE = {'claude-config-testing.md'}  # su versión general es .agents/rules/agent-config-testing.md
_FRONT = re.compile(r'\A---\n.*?\n---\n\n?', re.DOTALL)


def split(text: str) -> tuple[str, str]:
    """(frontmatter con sus rayas, cuerpo).

    >>> split('---\\ntrigger: always_on\\n---\\n\\n# R\\n')
    ('---\\ntrigger: always_on\\n---\\n\\n', '# R\\n')
    >>> split('# R\\n')
    ('', '# R\\n')
    """
    m = _FRONT.match(text)
    return (m.group(0), text[m.end() :]) if m else ('', text)


def pares(root: Path) -> list[tuple[Path, Path, bool]]:
    """(fuente, copia, solo_cuerpo) de cada regla y skill de .agents/."""
    out = [(f, root / '.claude/rules' / f.name, True) for f in sorted((root / '.agents/rules').glob('*.md'))]
    for s in sorted((root / '.agents/skills').glob('*/SKILL.md')):
        out.append((s, root / '.claude/skills' / s.parent.name / 'SKILL.md', False))
    return out


def differences(root: Path) -> list[str]:
    """Copias de .claude/ que faltan o cuyo cuerpo no coincide, y reglas de .claude/ sin fuente en .agents/."""
    out = []
    for source, copy, body in pares(root):
        if not copy.is_file():
            out.append(f'missing {copy.relative_to(root).as_posix()}')
            continue
        a, b = source.read_text(encoding='utf-8'), copy.read_text(encoding='utf-8')
        if (split(a)[1] != split(b)[1]) if body else a != b:
            out.append(f'{copy.relative_to(root).as_posix()} differs from {source.relative_to(root).as_posix()}')
    sources = {f.name for f in (root / '.agents/rules').glob('*.md')} | ONLY_CLAUDE
    claude = sorted((root / '.claude/rules').glob('*.md'))
    out += [f'.claude/rules/{c.name} has no source in .agents/rules/' for c in claude if c.name not in sources]
    return out


def sync(root: Path) -> list[str]:
    """Reescribe las copias de .claude/ desde .agents/; devuelve las que cambió."""
    changed = []
    for source, copy, body in pares(root):
        text = source.read_text(encoding='utf-8')
        if body:
            previous = copy.read_text(encoding='utf-8') if copy.is_file() else ''
            text = split(previous)[0] + split(text)[1]
        if not copy.is_file() or copy.read_text(encoding='utf-8') != text:
            copy.parent.mkdir(parents=True, exist_ok=True)
            copy.write_text(text, encoding='utf-8', newline='\n')
            changed.append(copy.relative_to(root).as_posix())
    return changed


def main(argv: list[str]) -> int:
    """Entrada de `python -m devtools rules`: compara o, con --sync, reescribe las copias de .claude/."""
    if argv not in ([], ['--sync']):
        print('usage: rules [--sync]', file=sys.stderr)
        return 0 if argv[:1] in (['-h'], ['--help']) else 2
    if argv:
        changed = sync(paths.ROOT)
        print(json.dumps({'synced': changed}, ensure_ascii=False))
        for c in changed:
            print(f'synced {c}', file=sys.stderr)
    missing = differences(paths.ROOT)
    if argv == []:
        print(json.dumps({'differences': missing}, ensure_ascii=False))
    for d in missing:
        print(f'FALLA {d}', file=sys.stderr)
    return 1 if missing else 0

"""`reglas [--sincronizar]`: las reglas y skills de .agents/ (fuente) y .claude/ (copia) tienen el mismo cuerpo.

Cada regla vive en `.agents/rules/<r>.md` con el frontmatter de Antigravity (`trigger`, `description`) y en
`.claude/rules/<r>.md` con el de Claude Code (`paths:` opcional; sin él, la regla carga siempre). Cada skill, igual en
`.agents/skills/<s>/SKILL.md` y `.claude/skills/<s>/SKILL.md`. Sin argumentos lista las diferencias (exit 1 si hay);
`--sincronizar` reescribe las copias de .claude/ desde .agents/ conservando su frontmatter.
Regla: agent-config-testing.md.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from . import rutas

SOLO_CLAUDE = {'claude-config-testing.md'}  # su versión general es .agents/rules/agent-config-testing.md
_FRONT = re.compile(r'\A---\n.*?\n---\n\n?', re.DOTALL)


def partir(texto: str) -> tuple[str, str]:
    """(frontmatter con sus rayas, cuerpo).

    >>> partir('---\\ntrigger: always_on\\n---\\n\\n# R\\n')
    ('---\\ntrigger: always_on\\n---\\n\\n', '# R\\n')
    >>> partir('# R\\n')
    ('', '# R\\n')
    """
    m = _FRONT.match(texto)
    return (m.group(0), texto[m.end() :]) if m else ('', texto)


def pares(raiz: Path) -> list[tuple[Path, Path, bool]]:
    """(fuente, copia, solo_cuerpo) de cada regla y skill de .agents/."""
    out = [(f, raiz / '.claude/rules' / f.name, True) for f in sorted((raiz / '.agents/rules').glob('*.md'))]
    for s in sorted((raiz / '.agents/skills').glob('*/SKILL.md')):
        out.append((s, raiz / '.claude/skills' / s.parent.name / 'SKILL.md', False))
    return out


def diferencias(raiz: Path) -> list[str]:
    """Copias de .claude/ que faltan o cuyo cuerpo no coincide, y reglas de .claude/ sin fuente en .agents/."""
    out = []
    for fuente, copia, cuerpo in pares(raiz):
        if not copia.is_file():
            out.append(f'falta {copia.relative_to(raiz).as_posix()}')
            continue
        a, b = fuente.read_text(encoding='utf-8'), copia.read_text(encoding='utf-8')
        if (partir(a)[1] != partir(b)[1]) if cuerpo else a != b:
            out.append(f'{copia.relative_to(raiz).as_posix()} difiere de {fuente.relative_to(raiz).as_posix()}')
    fuentes = {f.name for f in (raiz / '.agents/rules').glob('*.md')} | SOLO_CLAUDE
    claude = sorted((raiz / '.claude/rules').glob('*.md'))
    out += [f'.claude/rules/{c.name} sin fuente en .agents/rules/' for c in claude if c.name not in fuentes]
    return out


def sincronizar(raiz: Path) -> list[str]:
    """Reescribe las copias de .claude/ desde .agents/; devuelve las que cambió."""
    cambiadas = []
    for fuente, copia, cuerpo in pares(raiz):
        texto = fuente.read_text(encoding='utf-8')
        if cuerpo:
            previo = copia.read_text(encoding='utf-8') if copia.is_file() else ''
            texto = partir(previo)[0] + partir(texto)[1]
        if not copia.is_file() or copia.read_text(encoding='utf-8') != texto:
            copia.parent.mkdir(parents=True, exist_ok=True)
            copia.write_text(texto, encoding='utf-8', newline='\n')
            cambiadas.append(copia.relative_to(raiz).as_posix())
    return cambiadas


def main(argv: list[str]) -> int:
    if argv not in ([], ['--sincronizar']):
        print('uso: reglas [--sincronizar]', file=sys.stderr)
        return 0 if argv[:1] in (['-h'], ['--help']) else 2
    if argv:
        cambiadas = sincronizar(rutas.RAIZ)
        print(json.dumps({'synced': cambiadas}, ensure_ascii=False))
        for c in cambiadas:
            print(f'sincronizada {c}', file=sys.stderr)
    faltan = diferencias(rutas.RAIZ)
    if argv == []:
        print(json.dumps({'differences': faltan}, ensure_ascii=False))
    for d in faltan:
        print(f'FALLA {d}', file=sys.stderr)
    return 1 if faltan else 0

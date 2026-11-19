"""`contexto-agentes`: mide las instrucciones que carga cada agente y sale con 1 si alguna pasa su límite.

Lo corre el pre-commit cuando hay archivos de instrucciones staged. Claude Code carga AGENTS.md/CLAUDE.md y las
reglas de .claude/rules/ sin `paths:` en cada sesión; Codex lee AGENTS.md hasta `project_doc_max_bytes`; Antigravity
trunca cada regla de .agents/rules/ y descarta sin avisar la que no tiene un `trigger` válido. Adaptado de klinikae.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from content_studio import rutas

LIMITES = {
    'regla': 15_000,  # caracteres por regla o instrucción del repo (decisión del proyecto)
    'claude-siempre': 80_000,  # caracteres de lo que Claude Code carga siempre desde el repo
    'codex': 32_768,  # bytes de AGENTS.md (project_doc_max_bytes por defecto)
    'agy-regla': 24_000,  # bytes por regla de Antigravity
}
TRIGGERS = {'always_on', 'model_decision', 'glob', 'manual'}


def frontmatter(texto: str) -> str:
    """Bloque YAML del inicio, sin las rayas; vacío si no hay.

    >>> frontmatter('---\\npaths:\\n  - a\\n---\\n# X'), frontmatter('# X')
    ('paths:\\n  - a', '')
    """
    m = re.match(r'---\n(.*?)\n---\n', texto, re.DOTALL)
    return m.group(1) if m else ''


def medir(raiz: Path) -> tuple[dict, list[str]]:
    """Tamaños por agente y la lista de fallos."""
    fallos: list[str] = []
    claude = [raiz / n for n in ('AGENTS.md', 'CLAUDE.md', 'CLAUDE.local.md') if (raiz / n).is_file()]
    reglas_claude = sorted((raiz / '.claude/rules').glob('**/*.md'))
    siempre = claude + [r for r in reglas_claude if 'paths:' not in frontmatter(r.read_text(encoding='utf-8'))]
    reglas_agy = sorted((raiz / '.agents/rules').glob('*.md'))
    for f in claude + reglas_claude + reglas_agy:
        n = len(f.read_text(encoding='utf-8'))
        if n > LIMITES['regla']:
            fallos.append(f'{f.relative_to(raiz).as_posix()}: {n} caracteres > {LIMITES["regla"]} (detalle a docs)')
    total = sum(len(f.read_text(encoding='utf-8')) for f in siempre)
    if total > LIMITES['claude-siempre']:
        fallos.append(f'Claude Code carga siempre {total} caracteres > {LIMITES["claude-siempre"]}')
    agents = raiz / 'AGENTS.md'
    codex = agents.stat().st_size if agents.is_file() else 0
    if codex > LIMITES['codex']:
        fallos.append(f'AGENTS.md: {codex} bytes > {LIMITES["codex"]} (Codex deja de leer)')
    for r in reglas_agy:
        datos = r.read_bytes()
        # Los bytes cuentan para el límite; el texto se normaliza (en Windows, git hace checkout con CRLF).
        texto = datos.decode('utf-8').replace('\r\n', '\n')
        trigger = re.search(r'^trigger:\s*(\S+)', frontmatter(texto), re.MULTILINE)
        if not trigger or trigger.group(1) not in TRIGGERS:
            fallos.append(f'{r.relative_to(raiz).as_posix()}: sin trigger válido ({", ".join(sorted(TRIGGERS))})')
        if len(datos) > LIMITES['agy-regla']:
            fallos.append(f'{r.relative_to(raiz).as_posix()}: {len(datos)} bytes > {LIMITES["agy-regla"]}')
    agentes = {
        'claude': {'files': len(siempre), 'chars': total},
        'codex': {'files': int(codex > 0), 'bytes': codex},
        'antigravity': {'files': len(reglas_agy), 'bytes': sum(r.stat().st_size for r in reglas_agy)},
    }
    return agentes, fallos


def main(argv: list[str]) -> int:
    if argv:
        print('uso: contexto-agentes (sin argumentos)', file=sys.stderr)
        return 0 if argv[0] in ('-h', '--help') else 2
    agentes, fallos = medir(rutas.RAIZ)
    print(json.dumps({'agents': agentes, 'failures': fallos}, ensure_ascii=False))
    for nombre, datos in agentes.items():
        print(f'{nombre}: {datos}', file=sys.stderr)
    for f in fallos:
        print(f'FALLA {f}', file=sys.stderr)
    return 1 if fallos else 0

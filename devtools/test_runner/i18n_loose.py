"""Textos sueltos (spec 007, AC-4 y AC-5, D-8): texto visible fuera de t() y de ApiError en la API y en el client.

«Qué cuenta como texto», la misma regla en Python y en client/scripts/loose-texts.ts (las dos la prueban con
devtools/tests/fixtures/i18n/prose-cases.json): un literal, sin los espacios del borde, con letras y una de estas
condiciones: dos palabras con letras separadas por espacio; una letra fuera de ASCII o ¿ ¡; una sola palabra con
mayúscula inicial y el resto en minúscula. Los ids (`lofi-chill`), las claves (`queue.title`), las constantes (`GET`),
los nombres en PascalCase (`ApiError`) y los atajos (`Ctrl+K`) no cuentan.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TypeGuard

from .. import paths

CONFIG = paths.ROOT / 'tests' / 'validators' / 'i18n.json'
MARKER = re.compile(r'#\s*i18n-ignore:(.*)$')
LOG_OBJECTS = frozenset({'log', 'logger', 'logging'})
SUBPROCESS_CALLS = frozenset({'Path', 'join', 'run', 'Popen', 'check_output', 'open', 'getenv'})
SQL_CALLS = frozenset({'execute', 'executemany', 'executescript'})  # el SQL no se muestra al usuario
API_ERRORS = frozenset({'ApiError', 'HTTPException'})


def is_prose(text: str) -> bool:
    """¿Es texto visible? La regla de la cabecera (la misma que loose-texts.ts)."""
    stripped = text.strip()
    if not any(char.isalpha() for char in stripped):
        return False
    if any(char in '¿¡' or (ord(char) > 127 and char.isalpha()) for char in stripped):
        return True
    words = stripped.split()
    if sum(1 for word in words if any(char.isalpha() for char in word)) >= 2:
        return True
    return len(words) == 1 and stripped[0].isupper() and stripped[1:].islower()


@dataclass(frozen=True)
class Finding:
    """Un texto suelto o un `i18n-ignore` sin motivo, con su archivo (para mostrar) y su línea."""

    path: str
    line: int
    text: str
    reason_missing: bool = False

    def message(self) -> str:
        """Una línea para la salida de la etapa, en inglés y accionable (textos-e-idioma.md)."""
        if self.reason_missing:
            return (
                f'{self.path}:{self.line}: i18n-ignore needs a reason: '
                'write "i18n-ignore: <why it is not visible text>".'
            )
        marker = '//' if self.path.endswith(('.ts', '.tsx')) else '#'
        return (
            f'{self.path}:{self.line}: loose text "{self.text}". Move it to messages/*.json and use t(\'…\'), '
            f'or mark the line with {marker} i18n-ignore: <reason>.'
        )


def _show(path: Path) -> str:
    try:
        return path.relative_to(paths.ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _is_text(node: ast.AST | None) -> TypeGuard[ast.Constant]:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def _subtree(node: ast.AST) -> set[int]:
    return {id(child) for child in ast.walk(node)}


def _skipped(tree: ast.Module) -> set[int]:
    """Los literales que no son texto visible: docstrings, logs, claves, códigos, subprocess e internos."""
    skip: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            first = node.body[0] if node.body else None
            if isinstance(first, ast.Expr) and _is_text(first.value):
                skip.add(id(first.value))
        elif isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values, strict=False):
                if _is_text(key):
                    skip.add(id(key))
                if _is_text(key) and key.value == 'code' and value is not None:
                    skip |= _subtree(value)
        elif isinstance(node, ast.Subscript):
            skip |= _subtree(node.slice)
        elif isinstance(node, ast.Call):
            callee = node.func
            name = callee.id if isinstance(callee, ast.Name) else getattr(callee, 'attr', '')
            owner = callee.value.id if isinstance(callee, ast.Attribute) and isinstance(callee.value, ast.Name) else ''
            is_super_init = (
                isinstance(callee, ast.Attribute) and callee.attr == '__init__' and isinstance(callee.value, ast.Call)
            )
            if owner in LOG_OBJECTS or name in SUBPROCESS_CALLS or name in SQL_CALLS or is_super_init:
                skip |= _subtree(node)
            elif name == 'ApiError' and len(node.args) >= 2:
                skip |= _subtree(node.args[1])
        elif isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
            callee = node.exc.func
            name = callee.id if isinstance(callee, ast.Name) else getattr(callee, 'attr', '')
            if name not in API_ERRORS:
                skip |= _subtree(node.exc)
    return skip


def check_loose_python(files: list[Path], allowed: frozenset[str] = frozenset()) -> list[Finding]:
    """Texto suelto en archivos de Python (con ast). Un `# i18n-ignore:` sin motivo es un hallazgo aparte."""
    findings: list[Finding] = []
    for file in files:
        source = file.read_text(encoding='utf-8')
        lines = source.splitlines()
        markers = {
            number: match.group(1).strip() for number, line in enumerate(lines, 1) if (match := MARKER.search(line))
        }
        for number, reason in markers.items():
            if not reason:
                findings.append(Finding(_show(file), number, '', reason_missing=True))
        tree = ast.parse(source)
        skip = _skipped(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            text = node.value.strip()
            if id(node) in skip or text in allowed or node.lineno in markers or not is_prose(text):
                continue
            findings.append(Finding(_show(file), node.lineno, text))
    return sorted(findings, key=lambda finding: (finding.path, finding.line))


MAX_TS_COMMAND_LENGTH = 16_000


def _ts_file_batches(files: list[Path], root: Path) -> list[list[Path]]:
    """Agrupa rutas antes de superar el límite de CreateProcess en Windows."""
    prefix = ['bun', 'run', '--cwd', str(root / 'client'), 'loose-texts']
    batches: list[list[Path]] = []
    batch: list[Path] = []
    for file in files:
        candidate = [*batch, file]
        command = [*prefix, *(str(path) for path in candidate)]
        if batch and len(subprocess.list2cmdline(command)) > MAX_TS_COMMAND_LENGTH:
            batches.append(batch)
            batch = [file]
        else:
            batch = candidate
    if batch:
        batches.append(batch)
    return batches


def check_loose_ts(files: list[Path], root: Path = paths.ROOT) -> list[Finding]:
    """Texto suelto en archivos de TS/TSX: corre client/scripts/loose-texts.ts con bun y lee su JSON."""
    prefix = ['bun', 'run', '--cwd', str(root / 'client'), 'loose-texts']
    findings: list[Finding] = []
    for batch in _ts_file_batches(files, root):
        command = [*prefix, *(str(file) for file in batch)]
        try:
            done = subprocess.run(command, capture_output=True, encoding='utf-8', errors='replace', check=False)
        except FileNotFoundError as error:
            raise RuntimeError('bun is not in PATH: install it, run `bun install`, and try again') from error
        if done.returncode != 0:
            raise RuntimeError((done.stderr or done.stdout).strip())
        findings.extend(
            Finding(_show(Path(row['path'])), row['line'], row['text'], row['reasonMissing'])
            for row in json.loads(done.stdout)
        )
    return findings


def check_loose(root: Path = paths.ROOT) -> list[Finding]:
    """Textos sueltos del repo: los archivos de `python.include` y los de client/src menos `ts.exclude`."""
    config = json.loads((root / 'tests' / 'validators' / 'i18n.json').read_text(encoding='utf-8'))
    allowed = frozenset(entry.strip() for entry in config['allowed'])
    python_files = [
        file
        for entry in config['python']['include']
        for file in ([root / entry] if (root / entry).is_file() else sorted((root / entry).rglob('*.py')))
    ]
    excluded = tuple(config['ts']['exclude'])
    ts_files = [
        file
        for file in sorted((root / 'client' / 'src').rglob('*'))
        if file.suffix in {'.ts', '.tsx'} and not file.name.endswith('.d.ts') and not _show(file).startswith(excluded)
    ]
    return check_loose_python(python_files, allowed) + check_loose_ts(ts_files, root)

"""Etiquetas nativas fuera de los átomos (spec 008, AC-2 y AC-4, D-5): la etapa `ui-structure` de devtools.

La regla vive en client/scripts/ui-structure.ts, con el compilador de TypeScript (la misma técnica que loose-texts.ts de
la 007). Aquí se elige qué archivos se miran y se da el mensaje. Los átomos y las primitivas de shadcn (las carpetas
`atoms/` y `shadcn/`) pueden usar etiquetas nativas; el resto no, y no hay marcador para excepciones: lo que haga falta
va a un átomo. `files` no cambia el resultado: la etapa revisa todo `client/src`.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .. import paths

# Las carpetas que sí pueden usar etiquetas nativas: los átomos y el código de shadcn (spec 008, D-5).
EXEMPT_FOLDERS = frozenset({'atoms', 'shadcn'})


@dataclass(frozen=True)
class Finding:
    """Un hallazgo: el archivo, la línea y la etiqueta nativa que no debe estar fuera de los átomos."""

    path: str
    line: int
    tag: str

    def message(self) -> str:
        """Una línea para la salida de la etapa, en inglés y accionable (textos-e-idioma.md)."""
        return (
            f'{self.path}:{self.line}: native <{self.tag}> outside atoms. '
            'Use a component from shared/components (UIButton, UIIconButton) or add one.'
        )


def is_exempt(path: Path, base: Path) -> bool:
    """¿Está en una carpeta `atoms/` o `shadcn/` bajo `base`? El nombre del archivo no cuenta."""
    return bool(EXEMPT_FOLDERS.intersection(path.relative_to(base).parts[:-1]))


def _show(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def check_ui_structure(
    files: list[Path],
    base: Path = paths.ROOT / 'client' / 'src',
    root: Path = paths.ROOT,
) -> list[Finding]:
    """Etiquetas nativas en `files` fuera de `atoms/` y `shadcn/` (bajo `base`): corre el script con bun."""
    client = root / 'client'
    scanned = [file for file in files if not is_exempt(file, base)]
    if not scanned:
        return []
    # Rutas relativas a client/ (desde ahí corre bun): así la línea de comandos queda corta.
    relative = [os.path.relpath(file, client) for file in scanned]
    command = ['bun', 'run', '--cwd', str(client), 'ui-structure', *relative]
    try:
        done = subprocess.run(command, capture_output=True, encoding='utf-8', errors='replace', check=False)
    except FileNotFoundError as error:
        raise RuntimeError('bun is not in PATH: install it, run `bun install`, and try again') from error
    if done.returncode != 0:
        raise RuntimeError((done.stderr or done.stdout).strip())
    return [
        Finding(_show(Path(os.path.normpath(client / row['path'])), root), row['line'], row['tag'])
        for row in json.loads(done.stdout)
    ]


def run(files: list[Path], root: Path = paths.ROOT) -> dict:
    """Etapa `ui-structure`: revisa todo client/src. `files` no cambia el resultado."""
    src = root / 'client' / 'src'
    try:
        problems = [finding.message() for finding in check_ui_structure(sorted(src.rglob('*.tsx')), src, root)]
    except RuntimeError as error:
        problems = [str(error)]
    return {'stage': 'ui-structure', 'status': 'fail' if problems else 'pass', 'detail': '\n'.join(problems)}

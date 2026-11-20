"""Traslada una carpeta y reescribe las instalaciones editables."""

from __future__ import annotations

import errno
import hashlib
import os
import shutil
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path


def _forms(path: Path) -> tuple[bytes, ...]:
    native = str(path)
    return tuple(value.encode() for value in (path.as_uri(), native.replace('\\', '\\\\'), native, path.as_posix()))


def rewrite_installs(
    root: Path, changes: Iterable[tuple[Path, Path]], undo: dict[Path, bytes] | None = None
) -> list[str]:
    """Actualiza .pth y direct_url.json, con respaldo opcional antes de cada escritura."""
    replacements = [
        (old, new) for source, target in changes for old, new in zip(_forms(source), _forms(target), strict=True)
    ]
    root = root.resolve()
    changed = []
    for venv in root.rglob('.venv*'):
        if not venv.is_dir() or venv.is_symlink():
            continue
        for site in (venv / 'Lib/site-packages', *venv.glob('lib/python*/site-packages')):
            for file in (*site.glob('*.pth'), *site.glob('*.dist-info/direct_url.json')):
                if file.is_symlink() or not file.resolve().is_relative_to(root):
                    continue
                original = updated = file.read_bytes()
                for old, new in replacements:
                    updated = updated.replace(old, new)
                if updated != original:
                    if undo is not None:
                        undo[file] = original
                    file.write_bytes(updated)
                    changed.append(str(file))
    return changed


def _digest(path: Path) -> bytes:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.digest()


def _copy_between_volumes(source: Path, target: Path, progress: Callable[[float], None]) -> None:
    total = sum(file.stat().st_size for file in source.rglob('*') if file.is_file() and not file.is_symlink())
    copied = 0

    def copy_verified(original: str, duplicate: str) -> str:
        nonlocal copied
        shutil.copy2(original, duplicate)
        first, second = Path(original), Path(duplicate)
        size = first.stat().st_size
        if size != second.stat().st_size or _digest(first) != _digest(second):
            raise OSError(f'Copy verification failed: {first}')
        copied += size
        progress(copied / max(total, 1))
        return duplicate

    with tempfile.TemporaryDirectory(dir=target.parent, prefix='.studio-move-') as temporary:
        staging = Path(temporary) / 'data'
        shutil.copytree(source, staging, symlinks=True, copy_function=copy_verified)
        rewrite_installs(staging, [(source, target)])
        os.rename(staging, target)


def move(source: Path, target: Path, save: Callable[[], None], progress: Callable[[float], None] | None = None) -> None:
    """Mueve los datos a un destino vacío y guarda el cambio cuando el destino está completo."""
    if source.is_symlink() or target.is_symlink():
        raise ValueError('Storage roots must be real directories')
    source, target = source.resolve(), target.resolve()
    if source.is_relative_to(target) or target.is_relative_to(source):
        raise ValueError('Storage directories must be separate')
    if source.exists() and not source.is_dir():
        raise ValueError('Storage source must be a directory')
    existed = target.exists()
    if existed:
        target.rmdir()  # Solo se acepta una carpeta vacía.
    target.parent.mkdir(parents=True, exist_ok=True)
    renamed, copied, created = False, False, False
    originals: dict[Path, bytes] = {}
    try:
        if source.exists():
            try:
                os.replace(source, target)
                renamed = True
            except OSError as error:
                # cspell:ignore EXDEV
                if error.errno != errno.EXDEV:
                    raise
                _copy_between_volumes(source, target, progress or (lambda fraction: None))
                copied = True
            if renamed:
                rewrite_installs(target, [(source, target)], originals)
        else:
            target.mkdir()
            created = True
        save()
    except BaseException:
        if renamed:
            os.rename(target, source)
            for file, original in originals.items():
                (source / file.relative_to(target)).write_bytes(original)
        elif copied:
            shutil.rmtree(target)
        elif created:
            target.rmdir()
        if existed:
            target.mkdir(exist_ok=True)
        raise
    if copied:
        shutil.rmtree(source)

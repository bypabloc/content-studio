"""Reubicar una carpeta de datos con la spec 012, AC-7."""

import errno
import hashlib
import os
from pathlib import Path

import pytest

from content_studio.storage import relocate


@pytest.fixture
def folders(tmp_path):
    """Una carpeta con pesos y un venv editable de prueba; el destino todavía no existe."""
    source = tmp_path / 'origin'
    target = tmp_path / 'destination'
    site = source / 'narration' / '.venv-test' / 'Lib/site-packages'
    site.mkdir(parents=True)
    pointer = site / 'engine.pth'
    pointer.write_text(str(source / 'narration/engines/engine') + '\n', encoding='utf-8')
    (source / 'weights.bin').write_bytes(b'fake weights')
    return source, target, pointer.relative_to(source)


def _force_cross_volume(monkeypatch, source):
    original = os.replace

    def replace(origin, target):
        if Path(origin) == source:
            # cspell:ignore EXDEV
            raise OSError(errno.EXDEV, 'different volume')
        original(origin, target)

    monkeypatch.setattr(os, 'replace', replace)


def test_ac7_same_volume_renames_and_rewrites_a_venv(folders):
    """El destino completo está disponible al guardar el cambio."""
    source, target, pointer = folders
    saved = []

    def save():
        assert (target / 'weights.bin').read_bytes() == b'fake weights'
        saved.append(target)

    relocate.move(source, target, save)

    assert saved == [target]
    assert str(target) in (target / pointer).read_text(encoding='utf-8')
    assert not source.exists()


def test_ac7_cross_volume_copies_before_committing(folders, monkeypatch):
    """La copia conserva el hash de los pesos y solo quita el origen al confirmar."""
    source, target, pointer = folders
    _force_cross_volume(monkeypatch, source)
    digest = hashlib.sha256((source / 'weights.bin').read_bytes()).digest()

    def save():
        assert source.exists()
        assert hashlib.sha256((target / 'weights.bin').read_bytes()).digest() == digest
        assert str(target) in (target / pointer).read_text(encoding='utf-8')

    relocate.move(source, target, save)

    assert not source.exists()


def test_ac7_failed_copy_preserves_the_origin(folders, monkeypatch):
    """La interrupción de una copia nunca cambia el origen ni publica un destino parcial."""
    source, target, pointer = folders
    _force_cross_volume(monkeypatch, source)
    original = (source / pointer).read_bytes()

    def fail_copy(*args, **kwargs):
        raise OSError('interrupted copy')

    monkeypatch.setattr(relocate.shutil, 'copy2', fail_copy)
    with pytest.raises(OSError, match='interrupted copy'):
        relocate.move(source, target, lambda: pytest.fail('committed an incomplete copy'))

    assert (source / pointer).read_bytes() == original
    assert (source / 'weights.bin').read_bytes() == b'fake weights'
    assert not target.exists()


def test_ac7_failed_commit_rolls_back_a_rename(folders):
    """Si falla el guardado de preferencias, el venv vuelve a apuntar al origen."""
    source, target, pointer = folders
    original = (source / pointer).read_bytes()

    def fail_commit():
        raise OSError('database write failed')

    with pytest.raises(OSError, match='database write failed'):
        relocate.move(source, target, fail_commit)

    assert (source / pointer).read_bytes() == original
    assert not target.exists()

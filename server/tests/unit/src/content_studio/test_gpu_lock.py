"""Candado de la GPU (spec 004, D-3, AC-4): se toma, se suelta y respeta a otra sesión (mismo formato que devtools)."""

from __future__ import annotations

import json
import os
import sys

from content_studio import gpu_lock


def _other_session_holds(main, work: str = 'otra') -> None:
    """Escribe el candado como `devtools gpu-turn`, con este proceso (vivo) como dueño."""
    file = gpu_lock.lock(main)
    file.parent.mkdir(parents=True, exist_ok=True)
    owner = {'pid': os.getpid(), 'platform': sys.platform, 'work': work, 'command': 'x', 'since': 't'}
    file.write_text(json.dumps(owner), encoding='utf-8')


def test_acquire_then_release_frees_the_lock(tmp_path):
    assert gpu_lock.acquire(tmp_path, 'job-1', ['cmd']) is True
    assert gpu_lock.read(tmp_path)['work'] == 'job-1'

    gpu_lock.release(tmp_path)

    assert gpu_lock.read(tmp_path) is None


def test_busy_lock_is_not_taken_without_waiting(tmp_path):
    _other_session_holds(tmp_path)

    assert gpu_lock.acquire(tmp_path, 'job-2', ['cmd'], wait=False) is False
    assert gpu_lock.read(tmp_path)['work'] == 'otra'


def test_orphan_lock_of_a_dead_process_is_cleared(tmp_path):
    file = gpu_lock.lock(tmp_path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps({'pid': 2**22 + 12345, 'platform': sys.platform, 'work': 'viejo'}), encoding='utf-8')

    assert gpu_lock.acquire(tmp_path, 'job-3', ['cmd']) is True
    gpu_lock.release(tmp_path)


def test_release_retries_when_the_lock_file_is_busy(tmp_path, monkeypatch):
    """Regresión: en Windows, un lector del candado abierto impide borrarlo; release lo reintenta."""
    assert gpu_lock.acquire(tmp_path, 'job-1', ['cmd']) is True
    real_unlink = type(tmp_path).unlink
    busy = [True]

    def unlink_busy_once(self, missing_ok=False):
        if busy[0]:
            busy[0] = False
            raise PermissionError(32, 'El proceso no tiene acceso al archivo')
        return real_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(type(tmp_path), 'unlink', unlink_busy_once)

    gpu_lock.release(tmp_path)

    assert gpu_lock.read(tmp_path) is None

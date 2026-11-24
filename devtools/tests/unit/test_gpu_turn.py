"""devtools gpu-turn: el turno de la GPU entre sesiones."""

from __future__ import annotations

import json
import sys

from devtools import gpu_turn


def test_gpu_turn_takes_releases_and_clears_orphans(tmp_path):
    assert gpu_turn.take(tmp_path, 't1', ['python', 'cli.py']) is None
    owner = gpu_turn.take(tmp_path, 't2', ['otro'])
    assert owner['work'] == 't1'  # ocupada por este mismo proceso
    gpu_turn.release(tmp_path)
    assert gpu_turn.read(tmp_path) is None
    orphan = {'pid': 2**22 + 12345, 'platform': sys.platform, 'work': 'viejo', 'command': 'x'}
    gpu_turn.lock(tmp_path).write_text(json.dumps(orphan))
    assert gpu_turn.read(tmp_path) is None  # su proceso murió
    assert gpu_turn.take(tmp_path, 't3', ['y']) is None
    gpu_turn.release(tmp_path)


def test_turn_gpu_of_other_sistema_counts_como_busy(tmp_path):
    lock = gpu_turn.lock(tmp_path)
    lock.parent.mkdir(parents=True)
    lock.write_text(json.dumps({'pid': 1, 'platform': 'otro-sistema', 'work': 'wsl'}))
    assert gpu_turn.read(tmp_path)['work'] == 'wsl'


def test_gpu_turn_run_releases_even_if_it_fails(tmp_path):
    assert gpu_turn.run(tmp_path, 't', [sys.executable, '-c', 'raise SystemExit(3)']) == 3
    assert not gpu_turn.lock(tmp_path).exists()

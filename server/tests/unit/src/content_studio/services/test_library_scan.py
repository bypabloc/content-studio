"""Servicio `library.scan` (spec 020, D-1): CPU, carpeta opcional y el módulo del escaneo."""

from __future__ import annotations

import sys
from pathlib import Path

from content_studio.services import library_scan


def test_scan_is_a_cpu_job():
    """Solo lee el disco y ffprobe: no toma el candado de la GPU."""
    assert library_scan.RESOURCE == 'cpu'


def test_validate_accepts_all_folders_or_one_folder_id():
    """Sin `folder_id` escanea todas; con uno, tiene que ser un entero positivo."""
    assert library_scan.validate({}) == []
    assert library_scan.validate({'folder_id': 3}) == []
    assert library_scan.validate({'folder_id': 'x'}) == [{'code': 'invalid_folder', 'params': {}}]


def test_build_command_runs_the_scan_module():
    """El comando es el módulo de escaneo; la base la recibe por `CONTENT_STUDIO_DB` del runner."""
    assert library_scan.build_command({}, Path('out')) == [sys.executable, '-m', 'content_studio.library.scan']
    assert library_scan.build_command({'folder_id': 2}, Path('out'))[-2:] == ['--folder', '2']

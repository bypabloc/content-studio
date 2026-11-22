"""Herramientas del sistema sin instalar programas ni cargar modelos, spec 012 AC-6."""

import os
import subprocess
import sys
from contextlib import nullcontext
from types import SimpleNamespace

from content_studio.system import tools


def test_ac6_install_ffmpeg_and_detect_it_from_the_registry(monkeypatch, tmp_path):
    """La detección usa el PATH actualizado sin reiniciar el proceso."""
    folder = str(tmp_path / 'winget')
    executable = str(tmp_path / 'winget' / 'ffmpeg.exe')
    calls = []

    def which(name, *, path=None):
        if name == 'winget':
            return 'winget'
        if name == 'ffmpeg' and folder in (path or os.environ['PATH']).split(os.pathsep):
            return executable
        return None

    def run(command, **options):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout='ffmpeg version 8.0\n', stderr='')

    monkeypatch.setenv('PATH', str(tmp_path))
    monkeypatch.setattr(tools.shutil, 'which', which)
    monkeypatch.setattr(tools.subprocess, 'run', run)
    monkeypatch.setattr(tools, 'windows_paths', lambda: [folder])

    assert tools.install_tool('ffmpeg')['installed'] is True
    assert calls[0] == [
        'winget',
        'install',
        '--id',
        'Gyan.FFmpeg',
        '-e',
        '--scope',
        'user',
        '--accept-package-agreements',
        '--accept-source-agreements',
    ]
    assert tools.detect()['ffmpeg'] == {'path': executable, 'version': 'ffmpeg version 8.0'}


def test_ac6_missing_winget_returns_manual_instructions(monkeypatch):
    """Las instrucciones están disponibles cuando falta el instalador."""
    monkeypatch.setattr(tools.shutil, 'which', lambda *args, **kwargs: None)
    monkeypatch.setattr(tools, 'windows_paths', lambda: [])

    result = tools.install_tool('ffmpeg')

    assert result['installed'] is False
    assert result['code'] == 'tool_install_failed'
    assert 'ffmpeg.org' in result['instructions']


def test_detect_reports_whether_the_ffmpeg_has_the_subtitles_filter(monkeypatch):
    """`detect()` informa si el ffmpeg trae el filtro `subtitles` (libass), con `ffmpeg -filters` (spec 014, D-7)."""

    class Done:
        returncode = 0

    binaries = {'ffmpeg': {'path': '/bin/ffmpeg', 'version': 'x'}, 'git': None}
    monkeypatch.setattr(tools, '_binary', lambda name, flag: binaries[name])
    monkeypatch.setattr(tools, '_gpu', lambda: None)

    Done.stdout = ' ... anull  A->A  Pass the source.\n T.. subtitles  V->V  Render subtitles.\n'
    monkeypatch.setattr(tools, '_run', lambda command, timeout=5: Done)
    assert tools.detect()['subtitles_filter'] is True

    Done.stdout = ' ... anull  A->A  Pass the source.\n'
    assert tools.detect()['subtitles_filter'] is False


def test_ac9_detect_returns_vram_in_gibibytes_without_loading_a_model(monkeypatch):
    """La detección de hardware usa información del driver."""

    def which(name, **kwargs):
        return 'nvidia-smi' if name == 'nvidia-smi' else None

    def run(command, **options):
        return subprocess.CompletedProcess(command, 0, stdout='NVIDIA RTX 4060, 8192 MiB, 580.00\n', stderr='')

    monkeypatch.setattr(tools.shutil, 'which', which)
    monkeypatch.setattr(tools.subprocess, 'run', run)
    monkeypatch.setattr(tools, 'windows_paths', lambda: [])

    assert tools.detect()['gpu'] == {'name': 'NVIDIA RTX 4060', 'vram_gb': 8.0, 'driver': '580.00', 'cuda': None}


def test_ac6_reads_registry_paths_from_machine_and_user(monkeypatch):
    """El registro puede aportar rutas instaladas después de abrir la app."""
    registry = SimpleNamespace(
        HKEY_LOCAL_MACHINE='machine',
        HKEY_CURRENT_USER='user',
        OpenKey=lambda hive, key: nullcontext(hive),
        QueryValueEx=lambda hive, field: (hive + ';extra', 0),
    )
    platform = SimpleNamespace(name='nt', path=os.path, pathsep=';')
    monkeypatch.setitem(sys.modules, 'winreg', registry)
    monkeypatch.setattr(tools, 'os', platform)

    assert tools.windows_paths() == ['machine', 'extra', 'user', 'extra']

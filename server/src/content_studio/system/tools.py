"""Detecta herramientas y GPU sin cargar modelos. Instala herramientas en Windows con winget."""

from __future__ import annotations

import csv
import os
import re
import shutil
import subprocess
from typing import TypedDict

PACKAGES = {'ffmpeg': 'Gyan.FFmpeg', 'git': 'Git.Git'}
HELP = {'ffmpeg': 'https://ffmpeg.org/download.html', 'git': 'https://git-scm.com/install/'}


class Binary(TypedDict):
    """Herramienta encontrada en el sistema."""

    path: str
    version: str


class GPU(TypedDict):
    """GPU reportada por su driver."""

    name: str
    vram_gb: float
    driver: str
    cuda: str | None


class System(TypedDict):
    """Instantánea del sistema disponible para el estudio."""

    ffmpeg: Binary | None
    git: Binary | None
    gpu: GPU | None


def windows_paths() -> list[str]:
    """Lee el PATH persistente que puede haber actualizado winget."""
    if os.name != 'nt':
        return []
    import winreg

    folders: list[str] = []
    for hive, key in (
        (winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'),
        (winreg.HKEY_CURRENT_USER, 'Environment'),
    ):
        try:
            with winreg.OpenKey(hive, key) as registry:
                raw = winreg.QueryValueEx(registry, 'Path')[0]
        except OSError:
            continue
        if isinstance(raw, str):
            folders.extend(os.path.expandvars(folder) for folder in raw.split(os.pathsep) if folder)
    return folders


def _refresh_path() -> None:
    registered = windows_paths()
    if registered:
        current = os.environ.get('PATH', '').split(os.pathsep)
        os.environ['PATH'] = os.pathsep.join(dict.fromkeys(folder for folder in current + registered if folder))


def _run(command: list[str], timeout: int | None = 5) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            errors='replace',
            timeout=timeout,
            check=False,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _binary(name: str, flag: str) -> Binary | None:
    executable = shutil.which(name)
    if not executable:
        return None
    result = _run([executable, flag])
    if result is None or result.returncode != 0 or not result.stdout.strip():
        return None
    return {'path': executable, 'version': result.stdout.splitlines()[0].strip()}


def _gpu() -> GPU | None:
    executable = shutil.which('nvidia-smi')
    if not executable:
        return None
    result = _run([executable, '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader'])
    if result is None or result.returncode:
        return None
    devices: list[GPU] = []
    for row in csv.reader(result.stdout.splitlines(), skipinitialspace=True):
        if len(row) != 3:
            continue
        name, memory, driver = (field.strip() for field in row)
        try:
            vram = float(memory.split()[0]) / 1024
        except (IndexError, ValueError):
            continue
        devices.append({'name': name, 'vram_gb': vram, 'driver': driver, 'cuda': None})
    if not devices:
        return None
    selected = max(devices, key=lambda device: device['vram_gb'])
    report = _run([executable])
    if report is not None and report.returncode == 0:
        cuda = re.search(r'CUDA Version:\s+([\d.]+)', report.stdout)
        if cuda:
            selected['cuda'] = cuda[1]
    return selected


def detect() -> System:
    """Detecta las herramientas ejecutables y la GPU con más VRAM."""
    _refresh_path()
    return {'ffmpeg': _binary('ffmpeg', '-version'), 'git': _binary('git', '--version'), 'gpu': _gpu()}


def winget_path() -> str | None:
    """Devuelve el ejecutable de winget si el sistema lo ofrece."""
    _refresh_path()
    return shutil.which('winget')


def install_tool(name: str) -> dict:
    """Instala la herramienta para el usuario y comprueba el PATH actualizado."""
    installer = winget_path()
    if installer:
        result = _run(
            [
                installer,
                'install',
                '--id',
                PACKAGES[name],
                '-e',
                '--scope',
                'user',
                '--accept-package-agreements',
                '--accept-source-agreements',
            ],
            timeout=None,
        )
        if result is not None:
            print(result.stdout, end='')
            print(result.stderr, end='')
        _refresh_path()
        installed = _binary(name, '-version' if name == 'ffmpeg' else '--version')
        if installed:
            return {'installed': True, **installed}
    return {'installed': False, 'code': 'tool_install_failed', 'instructions': HELP[name]}

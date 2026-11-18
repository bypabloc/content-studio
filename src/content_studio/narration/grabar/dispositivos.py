"""Micrófonos del equipo y los flags de entrada de ffmpeg para grabar de ellos. Solo stdlib + ffmpeg."""

from __future__ import annotations

import os
import re
import subprocess

WINDOWS = os.name == 'nt'


def fuentes() -> list[tuple[str, str, bool]]:
    """Micrófonos activos (Windows) o fuentes de PulseAudio/PipeWire (Linux, WSL)."""
    if WINDOWS:
        return microfonos_windows()
    r = subprocess.run(['ffmpeg', '-hide_banner', '-sources', 'pulse'], capture_output=True, text=True)
    return parsear_fuentes(r.stdout + r.stderr)


def microfonos_windows() -> list[tuple[str, str, bool]]:
    """Micrófonos activos según el registro (MMDevices), con el nombre que usa DirectShow: "<desc> (<interfaz>)".
    No se listan con `ffmpeg -list_devices true -f dshow`, porque ffmpeg se cae (0xC0000005) al enumerar
    algunas cámaras virtuales antes de llegar al audio."""
    import winreg

    base = r'SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Capture'
    lista = []
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base) as k:
        for i in range(winreg.QueryInfoKey(k)[0]):
            with winreg.OpenKey(k, winreg.EnumKey(k, i)) as d, winreg.OpenKey(d, 'Properties') as p:
                if winreg.QueryValueEx(d, 'DeviceState')[0] != 1:  # 1 = activo; desactivado/desconectado no
                    continue
                desc = winreg.QueryValueEx(p, '{a45c254e-df1c-4efd-8020-67d146a850e0},2')[0]
                interfaz = winreg.QueryValueEx(p, '{b3f8fa53-0004-438e-9003-51a46e139bfc},6')[0]
                lista.append((f'{desc} ({interfaz})', 'DirectShow', False))
    return sorted(lista)


def entrada(fuente: str) -> list[str]:
    """Flags de entrada de ffmpeg para grabar de `fuente`. En DirectShow, un búfer de 50 ms para que el
    vúmetro no vaya medio segundo atrasado."""
    if WINDOWS:
        return ['-f', 'dshow', '-audio_buffer_size', '50', '-i', f'audio={fuente}']
    return ['-f', 'pulse', '-i', fuente]


def parsear_fuentes(texto: str) -> list[tuple[str, str, bool]]:
    """(nombre, descripción, predeterminada) de cada fuente. El * marca la predeterminada.

    >>> parsear_fuentes('Auto-detected sources for pulse:\\n  RDPSink.monitor [Monitor of RDP Sink] (none)'
    ...                 '\\n* RDPSource [RDP Source] (none)')
    [('RDPSink.monitor', 'Monitor of RDP Sink', False), ('RDPSource', 'RDP Source', True)]
    """
    return [(m[2], m[3], m[1] == '*') for m in re.finditer(r'^(\*?)\s*(\S+)\s+\[(.*?)\]', texto, re.M)]

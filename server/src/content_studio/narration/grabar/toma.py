"""Una toma: ffmpeg graba el WAV y manda una copia a 16 kHz por la tubería para el medidor en vivo."""

from __future__ import annotations

import math
import queue
import subprocess
import threading
from array import array
from pathlib import Path

from rich.align import Align
from rich.live import Live

from content_studio.narration.grabar.dispositivos import entry
from content_studio.narration.grabar.interfaz import console, key_parar, keyboard_raw, view_recording

# Medidor en vivo: ffmpeg manda una copia a 16 kHz por la tubería; un bloque son 50 ms.
SAMPLING, BLOCK_S = 16000, 0.05


def grabar_take(source: str, destination: Path, style: str, n: int, text: str) -> tuple[bool, list[float]]:
    """Graba desde `fuente` hasta Enter, espacio o Ctrl+C, con el panel en vivo. ffmpeg escribe el WAV y
    manda una copia a 16 kHz por stdout para medir el nivel; se cierra limpio con 'q'.
    Devuelve (llegó audio, niveles en dB por bloque de 50 ms)."""
    proc = subprocess.Popen(
        ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *entry(source),
         '-map', '0:a', '-ac', '1', '-ar', '48000', '-c:a', 'pcm_s24le', str(destination),
         '-map', '0:a', '-ac', '1', '-ar', str(SAMPLING), '-f', 's16le', 'pipe:1'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    )  # fmt: skip
    block = int(SAMPLING * BLOCK_S) * 2
    levels: list[float] = []
    pending = b''
    # Un hilo lee el audio: select() no sirve con tuberías en Windows. b'' marca que ffmpeg terminó.
    cola: queue.Queue[bytes] = queue.Queue()

    def leer():
        try:
            while datum := proc.stdout.read1(8192):
                cola.put(datum)
        except (OSError, ValueError):  # communicate() cerró la tubería al parar
            pass
        cola.put(b'')

    threading.Thread(target=leer, daemon=True).start()

    def view():
        return Align.center(
            view_recording(style, n, text, len(levels) * BLOCK_S, levels),
            vertical='middle',
            height=console.size.height,
        )

    try:
        # Pantalla alternativa: cada frame se dibuja desde la esquina, sin mover el cursor relativo, así que
        # no deja restos aunque la terminal maneje distinto las líneas de ancho completo. Al parar, vuelve.
        with keyboard_raw(), Live(view(), console=console, refresh_per_second=20, screen=True) as live:
            finished = False
            while not finished and not key_parar():
                try:
                    data = [cola.get(timeout=BLOCK_S)]
                    while not cola.empty():
                        data.append(cola.get_nowait())
                except queue.Empty:
                    data = []
                for datum in data:
                    if not datum:
                        finished = True  # ffmpeg terminó solo: el dispositivo se cerró
                        break
                    pending += datum
                    while len(pending) >= block:
                        samples = array('h', pending[:block])
                        pending = pending[block:]
                        peak = max(max(samples), -min(samples), 1)
                        levels.append(20 * math.log10(peak / 32768))
                live.update(view())
    except KeyboardInterrupt:
        pass
    finally:
        try:
            proc.stdin.write(b'q')
            proc.stdin.flush()
            proc.communicate(timeout=10)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            proc.kill()
            proc.wait()
    return destination.exists() and destination.stat().st_size > 4096, levels

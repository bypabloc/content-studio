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

from content_studio.narration.grabar.dispositivos import entrada
from content_studio.narration.grabar.interfaz import console, tecla_parar, teclado_crudo, vista_grabacion

# Medidor en vivo: ffmpeg manda una copia a 16 kHz por la tubería; un bloque son 50 ms.
MUESTREO, BLOQUE_S = 16000, 0.05


def grabar_toma(fuente: str, destino: Path, estilo: str, n: int, texto: str) -> tuple[bool, list[float]]:
    """Graba desde `fuente` hasta Enter, espacio o Ctrl+C, con el panel en vivo. ffmpeg escribe el WAV y
    manda una copia a 16 kHz por stdout para medir el nivel; se cierra limpio con 'q'.
    Devuelve (llegó audio, niveles en dB por bloque de 50 ms)."""
    proc = subprocess.Popen(
        ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *entrada(fuente),
         '-map', '0:a', '-ac', '1', '-ar', '48000', '-c:a', 'pcm_s24le', str(destino),
         '-map', '0:a', '-ac', '1', '-ar', str(MUESTREO), '-f', 's16le', 'pipe:1'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
    )  # fmt: skip
    bloque = int(MUESTREO * BLOQUE_S) * 2
    niveles: list[float] = []
    pendiente = b''
    # Un hilo lee el audio: select() no sirve con tuberías en Windows. b'' marca que ffmpeg terminó.
    cola: queue.Queue[bytes] = queue.Queue()

    def leer():
        try:
            while dato := proc.stdout.read1(8192):
                cola.put(dato)
        except (OSError, ValueError):  # communicate() cerró la tubería al parar
            pass
        cola.put(b'')

    threading.Thread(target=leer, daemon=True).start()

    def vista():
        return Align.center(
            vista_grabacion(estilo, n, texto, len(niveles) * BLOQUE_S, niveles),
            vertical='middle',
            height=console.size.height,
        )

    try:
        # Pantalla alternativa: cada frame se dibuja desde la esquina, sin mover el cursor relativo, así que
        # no deja restos aunque la terminal maneje distinto las líneas de ancho completo. Al parar, vuelve.
        with teclado_crudo(), Live(vista(), console=console, refresh_per_second=20, screen=True) as live:
            terminado = False
            while not terminado and not tecla_parar():
                try:
                    datos = [cola.get(timeout=BLOQUE_S)]
                    while not cola.empty():
                        datos.append(cola.get_nowait())
                except queue.Empty:
                    datos = []
                for dato in datos:
                    if not dato:
                        terminado = True  # ffmpeg terminó solo: el dispositivo se cerró
                        break
                    pendiente += dato
                    while len(pendiente) >= bloque:
                        muestras = array('h', pendiente[:bloque])
                        pendiente = pendiente[bloque:]
                        pico = max(max(muestras), -min(muestras), 1)
                        niveles.append(20 * math.log10(pico / 32768))
                live.update(vista())
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
    return destino.exists() and destino.stat().st_size > 4096, niveles

"""Audio de la toma: recorte de bordes, velocidad (atempo), unión con pausas y masterización (§7.1)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from content_studio.comun.ffmpeg import ffmpeg, json_loudnorm, loudness


def recortar(audio, sr: int, umbral: float = 0.01, margen: float = 0.08):
    """Quita el silencio y el ruido bajo que el modelo deja en los bordes de cada bloque (de
    0.5 s a más de 2 s), para que las pausas insertadas duren lo indicado. Deja `margen` s para
    no cortar consonantes.

    >>> import numpy as np
    >>> x = np.r_[np.zeros(1000), np.full(500, 0.5), np.zeros(1000)].astype(np.float32)
    >>> len(recortar(x, 1000))
    660
    >>> len(recortar(np.zeros(100, dtype=np.float32), 1000))
    0
    >>> cola = np.r_[np.full(500, 0.5), np.full(2000, 0.004), [0.012], np.zeros(10)].astype(np.float32)
    >>> len(recortar(cola, 1000))  # ruido de cola con un pico suelto: no es voz
    580
    """
    import numpy as np

    # RMS por ventanas de 20 ms: un pico suelto en el ruido de cola no cuenta como voz.
    n = max(1, int(sr * 0.02))
    k = len(audio) // n
    rms = np.sqrt((audio[: k * n].reshape(k, n).astype(np.float64) ** 2).mean(axis=1))
    voz = np.flatnonzero(rms > umbral)
    if not voz.size:
        return audio[:0]
    m = int(sr * margen)
    return audio[max(0, voz[0] * n - m) : (voz[-1] + 1) * n + m]


def estirar(audio, sr: int, vel: float):
    """Cambia la velocidad sin cambiar el tono: ffmpeg atempo por tuberías."""
    import numpy as np

    if vel == 1.0 or not len(audio):
        return audio
    salida = subprocess.run(
        [
            'ffmpeg',
            '-loglevel',
            'error',
            '-f',
            'f32le',
            '-ar',
            str(sr),
            '-ac',
            '1',
            '-i',
            'pipe:0',
            '-filter:a',
            f'atempo={vel}',
            '-f',
            'f32le',
            'pipe:1',
        ],
        input=np.asarray(audio, dtype=np.float32).tobytes(),
        capture_output=True,
        check=True,
    ).stdout
    return np.frombuffer(salida, dtype=np.float32)


def escribir(g: dict) -> None:
    """Une los bloques con sus pausas, cada uno a la velocidad de su estilo, y guarda dónde empieza y
    termina cada bloque en el audio final (g['bloques'])."""
    import numpy as np
    import soundfile as sf

    sr, salida = g['sr'], g['salida']
    partes, g['bloques'], t = [], [], 0
    for voz, b, pb in zip(g['audios'], g['segs'], g['pb'], strict=False):
        vel = pb['p']['velocidad']
        voz = estirar(voz, sr, vel)
        cola = estirar(np.zeros(int(sr * b['pausa']), dtype=np.float32), sr, vel)
        g['bloques'].append((b['texto'], t / sr, (t + len(voz)) / sr))
        t += len(voz) + len(cola)
        partes += [voz, cola]
    audio = np.concatenate(partes)

    salida.parent.mkdir(parents=True, exist_ok=True)
    if g['master'] == 'voz' and np.abs(audio).max(initial=0) > 1e-4:
        g['master_info'] = masterizar(audio, sr, salida, g['lufs'])
    else:
        sf.write(salida, audio, sr, subtype='PCM_24')
        g['master_info'] = {'modo': 'no'}


def masterizar(audio, sr: int, salida: Path, lufs: float) -> dict:
    """Masterización 'voz' (§7.1): pasa-altos de 70 Hz y loudness lineal de dos pasadas hacia `lufs`, con techo de
    pico de −1.5 dBTP. Solo se limita la dinámica si el pico real no deja llegar a `lufs` (queda 'dynamic' y se
    avisa). Escribe WAV de 24 bits a la frecuencia nativa y devuelve lo medido."""
    import soundfile as sf

    crudo = salida.with_suffix('.crudo.wav')
    sf.write(crudo, audio, sr, subtype='FLOAT')
    base = f'highpass=f=70,loudnorm=I={lufs}'
    try:
        # Pasada 1: medir. Pasada 2: aplicar esa ganancia a la frecuencia nativa (loudnorm sobremuestrea a 192 kHz).
        medir = f'{base}:TP=-1.5:LRA=11:print_format=json'
        med = json_loudnorm(ffmpeg('-i', str(crudo), '-af', medir, '-f', 'null', '-'))
        tp = -1.5
        for _ in range(3):
            filtro = (
                f'{base}:TP={tp}:LRA=11:linear=true:measured_I={med["input_i"]}:measured_TP={med["input_tp"]}'
                f':measured_LRA={med["input_lra"]}:measured_thresh={med["input_thresh"]}'
                f':offset={med["target_offset"]}:print_format=json,aresample={sr}'
            )
            fin = json_loudnorm(ffmpeg('-y', '-i', str(crudo), '-af', filtro, '-c:a', 'pcm_s24le', str(salida)))
            final, pico = loudness(salida)
            if pico <= -1.5:
                break
            # El limitador dinámico se pasa unas décimas: se baja el techo en lo que sobró, con un margen.
            tp = round(tp - (pico + 1.5 + 0.05), 2)
            print(f'Aviso: pico real {pico} dBTP sobre -1.5; se repite con techo {tp} dBTP.')
    finally:
        crudo.unlink(missing_ok=True)
    tipo = 'linear' if fin['normalization_type'] == 'linear' else 'dynamic'
    if tipo == 'dynamic':
        print(f'Aviso: el pico real no deja llegar a {lufs} LUFS con ganancia lineal; se normalizó con dinámica.')
    if abs(final - lufs) > 0.5 or pico > -1.5:
        print(f'Aviso: masterización fuera de criterio: {final} LUFS (objetivo {lufs}), pico real {pico} dBTP.')
    return {
        'modo': 'voz',
        'lufs_objetivo': lufs,
        'lufs_final': final,
        'pico_real_final': pico,
        'tipo': tipo,
        'techo_tp': tp,
    }

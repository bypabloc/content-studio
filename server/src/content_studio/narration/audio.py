"""Audio de la toma: recorte de bordes, velocidad (atempo), unión con pausas y masterización (§7.1)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from content_studio.common.ffmpeg import ffmpeg, json_loudnorm, loudness

if TYPE_CHECKING:
    import numpy as np


def trim(audio: np.ndarray, sr: int, threshold: float = 0.01, margin: float = 0.08) -> np.ndarray:
    """Quita el silencio y el ruido bajo que el modelo deja en los bordes de cada bloque (de
    0.5 s a más de 2 s), para que las pausas insertadas duren lo indicado. Deja `margen` s para
    no cortar consonantes.

    >>> import numpy as np
    >>> x = np.r_[np.zeros(1000), np.full(500, 0.5), np.zeros(1000)].astype(np.float32)
    >>> len(trim(x, 1000))
    660
    >>> len(trim(np.zeros(100, dtype=np.float32), 1000))
    0
    >>> cola = np.r_[np.full(500, 0.5), np.full(2000, 0.004), [0.012], np.zeros(10)].astype(np.float32)
    >>> len(trim(cola, 1000))  # noise de cola con un peak suelto: no es voice
    580
    """
    import numpy as np

    # RMS por ventanas de 20 ms: un pico suelto en el ruido de cola no cuenta como voz.
    n = max(1, int(sr * 0.02))
    k = len(audio) // n
    rms = np.sqrt((audio[: k * n].reshape(k, n).astype(np.float64) ** 2).mean(axis=1))
    voice = np.flatnonzero(rms > threshold)
    if not voice.size:
        return audio[:0]
    m = int(sr * margin)
    return audio[max(0, voice[0] * n - m) : (voice[-1] + 1) * n + m]


def stretch(audio: np.ndarray, sr: int, vel: float) -> np.ndarray:
    """Cambia la velocidad sin cambiar el tono: ffmpeg atempo por tuberías."""
    import numpy as np

    if vel == 1.0 or not len(audio):
        return audio
    output = subprocess.run(
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
    return np.frombuffer(output, dtype=np.float32)


def write(g: dict) -> None:
    """Une los bloques con sus pausas, cada uno a la velocidad de su estilo, y guarda dónde empieza y
    termina cada bloque en el audio final (g['bloques'])."""
    import numpy as np
    import soundfile as sf

    sr, output = g['sr'], g['output']
    parts, g['blocks'], t = [], [], 0
    for voice, b, pb in zip(g['audios'], g['secs'], g['pb'], strict=False):
        vel = pb['p']['speed']
        voice = stretch(voice, sr, vel)
        cola = stretch(np.zeros(int(sr * b['pause']), dtype=np.float32), sr, vel)
        g['blocks'].append((b['text'], t / sr, (t + len(voice)) / sr))
        t += len(voice) + len(cola)
        parts += [voice, cola]
    audio = np.concatenate(parts)

    output.parent.mkdir(parents=True, exist_ok=True)
    if g['master'] == 'voice' and np.abs(audio).max(initial=0) > 1e-4:
        g['master_info'] = master(audio, sr, output, g['lufs'])
    else:
        sf.write(output, audio, sr, subtype='PCM_24')
        g['master_info'] = {'mode': 'no'}


def master(audio: np.ndarray, sr: int, output: Path, lufs: float) -> dict:
    """Masterización 'voz' (§7.1): pasa-altos de 70 Hz y loudness lineal de dos pasadas hacia `lufs`, con techo de
    pico de −1.5 dBTP. Solo se limita la dinámica si el pico real no deja llegar a `lufs` (queda 'dynamic' y se
    avisa). Escribe WAV de 24 bits a la frecuencia nativa y devuelve lo medido."""
    import soundfile as sf

    raw = output.with_suffix('.raw.wav')
    sf.write(raw, audio, sr, subtype='FLOAT')
    base = f'highpass=f=70,loudnorm=I={lufs}'
    try:
        # Pasada 1: medir. Pasada 2: aplicar esa ganancia a la frecuencia nativa (loudnorm sobremuestrea a 192 kHz).
        measure = f'{base}:TP=-1.5:LRA=11:print_format=json'
        med = json_loudnorm(ffmpeg('-i', str(raw), '-af', measure, '-f', 'null', '-'))
        tp = -1.5
        for _ in range(3):
            filter = (
                f'{base}:TP={tp}:LRA=11:linear=true:measured_I={med["input_i"]}:measured_TP={med["input_tp"]}'
                f':measured_LRA={med["input_lra"]}:measured_thresh={med["input_thresh"]}'
                f':offset={med["target_offset"]}:print_format=json,aresample={sr}'
            )
            end = json_loudnorm(ffmpeg('-y', '-i', str(raw), '-af', filter, '-c:a', 'pcm_s24le', str(output)))
            final, peak = loudness(output)
            if peak <= -1.5:
                break
            # El limitador dinámico se pasa unas décimas: se baja el techo en lo que sobró, con un margen.
            tp = round(tp - (peak + 1.5 + 0.05), 2)
            print(f'Notice: true peak {peak} dBTP above -1.5; retrying with ceiling {tp} dBTP.')
    finally:
        raw.unlink(missing_ok=True)
    kind = 'linear' if end['normalization_type'] == 'linear' else 'dynamic'
    if kind == 'dynamic':
        print(f'Notice: the true peak does not allow reaching {lufs} LUFS with linear gain; normalized with dynamics.')
    if abs(final - lufs) > 0.5 or peak > -1.5:
        print(f'Notice: mastering out of spec: {final} LUFS (target {lufs}), true peak {peak} dBTP.')
    return {
        'mode': 'voice',
        'target_lufs': lufs,
        'lufs_final': final,
        'peak_real_final': peak,
        'kind': kind,
        'ceiling_tp': tp,
    }

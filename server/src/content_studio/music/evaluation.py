"""Recorte del silencio final (ffmpeg) y detección de voz con demucs (--evaluate, solo en el venv de acestep)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

SILENCE_DB = -50  # por debajo de esto, la cola final se considera silencio y se recorta

# --evaluate: demucs separa el stem de voz; si suena por encima del umbral, la pista tiene voz.
# Whisper se descartó: alucina frases ("Outro Music") sobre música instrumental.
VOICE_MAX_DB = -25  # criterio: voz relativa a la mezcla. Medido: instrumentales de -35 a -44, cantada -5


def trim_silence(path: Path) -> float:
    """Quita la cola final por debajo de SILENCIO_DB, en el lugar. Devuelve los segundos que quedan."""
    tmp = path.with_suffix('.recorte.wav')
    audio_filter = f'areverse,silenceremove=start_periods=1:start_threshold={SILENCE_DB}dB,areverse'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', path, '-af', audio_filter, tmp], check=True)
    tmp.replace(path)
    dur = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return float(dur)


def voice_relative_db(model: Any, path: Path) -> float:
    """Nivel del stem de voz (htdemucs) respecto de la mezcla, en dB. ~0 = canta; muy negativo = instrumental."""
    import soundfile as sf
    import torch
    import torchaudio
    from demucs.apply import apply_model

    data, sr = sf.read(path, dtype='float32', always_2d=True)  # soundfile: torchaudio.load exige torchcodec
    wav = torchaudio.functional.resample(torch.from_numpy(data.T), sr, model.samplerate)
    ref = wav.mean(0)  # demucs separa mal sin esta normalización (todo salía a -75 dB)
    with torch.no_grad():
        sources = apply_model(model, ((wav - ref.mean()) / ref.std())[None], device='cuda', split=True)[0]
    voice = sources[model.sources.index('vocals')] * ref.std() + ref.mean()

    def rms_db(x: Any) -> float:
        return 20 * torch.log10(x.pow(2).mean().sqrt() + 1e-9).item()

    return rms_db(voice) - rms_db(wav)


def free_gpu() -> None:
    """Demucs necesita la VRAM que dejó el modelo de música."""
    import gc

    import torch

    gc.collect()
    torch.cuda.empty_cache()


def with_voice(outputs: list[Path]) -> list[Path]:
    """Devuelve las pistas donde se oye una voz (demucs, un solo modelo cargado).
    Una pista que no existe (la generación falló) también se devuelve, para reintentarla."""
    from demucs.pretrained import get_model

    print(f'Evaluando {len(outputs)} pista(s) con demucs (umbral {VOICE_MAX_DB} dB)...', flush=True)
    model = get_model('htdemucs').eval()
    bad = []
    for s in outputs:
        if not s.exists():
            print(f'  FALTA {s.name}: no se generó')
            bad.append(s)
            continue
        db = voice_relative_db(model, s)
        con = db > VOICE_MAX_DB
        print(f'  {"VOZ " if con else "ok  "} {s.name}: voz {db:.1f} dB respecto de la mezcla')
        bad += [s] if con else []
    return bad

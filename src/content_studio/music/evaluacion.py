"""Recorte del silencio final (ffmpeg) y detección de voz con demucs (--evaluar, solo en el venv de acestep)."""

from __future__ import annotations

import subprocess
from pathlib import Path

SILENCIO_DB = -50  # por debajo de esto, la cola final se considera silencio y se recorta

# --evaluar: demucs separa el stem de voz; si suena por encima del umbral, la pista tiene voz.
# Whisper se descartó: alucina frases ("Outro Music") sobre música instrumental.
VOZ_MAX_DB = -25  # criterio: voz relativa a la mezcla. Medido: instrumentales de -35 a -44, cantada -5


def recortar_silencio(ruta: Path) -> float:
    """Quita la cola final por debajo de SILENCIO_DB, en el lugar. Devuelve los segundos que quedan."""
    tmp = ruta.with_suffix('.recorte.wav')
    filtro = f'areverse,silenceremove=start_periods=1:start_threshold={SILENCIO_DB}dB,areverse'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', ruta, '-af', filtro, tmp], check=True)
    tmp.replace(ruta)
    dur = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', ruta],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return float(dur)


def voz_relativa_db(modelo, ruta: Path) -> float:
    """Nivel del stem de voz (htdemucs) respecto de la mezcla, en dB. ~0 = canta; muy negativo = instrumental."""
    import soundfile as sf
    import torch
    import torchaudio
    from demucs.apply import apply_model

    datos, sr = sf.read(ruta, dtype='float32', always_2d=True)  # soundfile: torchaudio.load exige torchcodec
    wav = torchaudio.functional.resample(torch.from_numpy(datos.T), sr, modelo.samplerate)
    ref = wav.mean(0)  # demucs separa mal sin esta normalización (todo salía a -75 dB)
    with torch.no_grad():
        fuentes = apply_model(modelo, ((wav - ref.mean()) / ref.std())[None], device='cuda', split=True)[0]
    voz = fuentes[modelo.sources.index('vocals')] * ref.std() + ref.mean()

    def rms_db(x) -> float:
        return 20 * torch.log10(x.pow(2).mean().sqrt() + 1e-9).item()

    return rms_db(voz) - rms_db(wav)


def liberar_gpu() -> None:
    """Demucs necesita la VRAM que dejó el modelo de música."""
    import gc

    import torch

    gc.collect()
    torch.cuda.empty_cache()


def con_voz(salidas: list[Path]) -> list[Path]:
    """Devuelve las pistas donde se oye una voz (demucs, un solo modelo cargado).
    Una pista que no existe (la generación falló) también se devuelve, para reintentarla."""
    from demucs.pretrained import get_model

    print(f'Evaluando {len(salidas)} pista(s) con demucs (umbral {VOZ_MAX_DB} dB)...', flush=True)
    modelo = get_model('htdemucs').eval()
    malas = []
    for s in salidas:
        if not s.exists():
            print(f'  FALTA {s.name}: no se generó')
            malas.append(s)
            continue
        db = voz_relativa_db(modelo, s)
        con = db > VOZ_MAX_DB
        print(f'  {"VOZ " if con else "ok  "} {s.name}: voz {db:.1f} dB respecto de la mezcla')
        malas += [s] if con else []
    return malas

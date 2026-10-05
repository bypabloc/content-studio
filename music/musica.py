"""Música instrumental local con ACE-Step 1.5 o HeartMuLa 3B, para GPU de 8 GB.

Uso:
    python music/musica.py --modelo acestep --estilo lofi-chill --duracion 60
    python music/musica.py --modelo acestep --duracion 30 --estilo corporate future-bass
    python music/musica.py --modelo acestep --duracion 30 --tono "E Minor" --bpm 105 \
        --estilo "synthwave, retro 80s, driving arpeggios"

--estilo acepta varios valores: un preset (ver ESTILOS) o texto libre, que se usa
tal cual como descripción. Cada preset define tonalidad, BPM y compás; el texto
libre los exige con --tono y --bpm. Estos flags también pisan los del preset.
El modelo se carga una vez y sale un .wav por estilo en --carpeta (out/music/
por defecto), con el silencio final ya recortado. Siempre instrumental. Los
pesos se descargan solos la primera vez a music/models/. Cada modelo corre en
su propio venv: music/.venv-acestep / music/.venv-heartmula (ver music/README.md).
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent  # music/: venvs y models/ viven aquí; salidas en out/music/
ACE_REPO = AQUI / 'models' / 'ACE-Step-1.5'
HEART_CKPT = AQUI / 'models' / 'heartmula-ckpt'

MODELOS = {
    'acestep': '.venv-acestep',
    'heartmula': '.venv-heartmula',
}

from estilos import ESTILOS  # catálogo: caption, tags (HeartMuLa), tono, bpm y compás de cada preset

SILENCIO_DB = -50  # por debajo de esto, la cola final se considera silencio y se recorta

# --evaluar: demucs separa el stem de voz; si suena por encima del umbral, la pista tiene voz.
# Whisper se descartó: alucina frases ("Outro Music") sobre música instrumental.
VOZ_MAX_DB = -25  # criterio: voz relativa a la mezcla. Medido: instrumentales de -35 a -44, cantada -5


def usar_venv(venv: str) -> None:
    destino = AQUI / venv
    if Path(sys.prefix).resolve() == destino.resolve():
        return
    py = destino / 'bin' / 'python'
    if not py.exists():
        sys.exit(f'Falta music/{venv}. Ver la instalación en music/README.md.')
    os.execv(py, [str(py), __file__, *sys.argv[1:]])


def resolver_estilo(valor: str, tono=None, bpm=None, compas=None) -> tuple[str, dict]:
    """Devuelve (nombre de archivo, estilo). Los flags pisan los metadatos del preset;
    el texto libre sirve de caption y de tags, y exige tono y bpm.

    >>> resolver_estilo('ambient')[1]['tono'], resolver_estilo('ambient', tono='Am', bpm=60)[1]['bpm']
    ('D Major', 60)
    >>> nombre, e = resolver_estilo('Synthwave, retro 80s!', tono='E Minor', bpm=105)
    >>> nombre, e['tags'], e['tono'], e['bpm'], e['compas']
    ('synthwave-retro-80s', 'Synthwave, retro 80s!', 'E Minor', 105, '4')
    >>> resolver_estilo('bossa nova')
    Traceback (most recent call last):
    SystemExit: "bossa nova" no es un preset: define --tono y --bpm (ej. --tono "C Major" --bpm 90)
    """
    if valor in ESTILOS:
        nombre, base = valor, ESTILOS[valor]
    else:
        if tono is None or bpm is None:
            sys.exit(f'"{valor}" no es un preset: define --tono y --bpm (ej. --tono "C Major" --bpm 90)')
        nombre = re.sub(r'[^a-z0-9]+', '-', valor.lower()).strip('-')[:60]
        base = dict(caption=valor, tags=valor, compas='4')
    pisar = {k: v for k, v in dict(tono=tono, bpm=bpm, compas=compas).items() if v is not None}
    return nombre, {**base, **pisar}


def recortar_silencio(ruta: Path) -> float:
    """Quita la cola final por debajo de SILENCIO_DB, en el lugar. Devuelve los segundos que quedan."""
    tmp = ruta.with_suffix('.recorte.wav')
    filtro = f'areverse,silenceremove=start_periods=1:start_threshold={SILENCIO_DB}dB,areverse'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', ruta, '-af', filtro, tmp], check=True)
    tmp.replace(ruta)
    dur = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', ruta],
        capture_output=True, text=True, check=True,
    ).stdout
    return float(dur)


def voz_relativa_db(modelo, ruta: Path) -> float:
    """Nivel del stem de voz (htdemucs) respecto de la mezcla, en dB. Cerca de 0 = canta; muy negativo = instrumental."""
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


def generar_acestep(trabajos, a) -> None:
    os.environ['ACESTEP_PROJECT_ROOT'] = str(ACE_REPO)
    from acestep.handler import AceStepHandler
    from acestep.inference import GenerationConfig, GenerationParams, generate_music
    from acestep.llm_inference import LLMHandler
    from acestep.model_downloader import ensure_lm_model, ensure_main_model

    ckpt = ACE_REPO / 'checkpoints'
    for ok, msg in [ensure_main_model(ckpt)] + ([] if a.sin_lm else [ensure_lm_model('acestep-5Hz-lm-0.6B', ckpt)]):
        if not ok:
            sys.exit(msg)

    # Perfil 6-8 GB de la guía oficial: DiT 2B turbo + LM 0.6B (backend pt) con offload.
    dit = AceStepHandler()
    dit.initialize_service(
        project_root=str(ACE_REPO), config_path='acestep-v15-turbo', device='cuda', offload_to_cpu=True,
    )
    llm = LLMHandler()
    if not a.sin_lm:
        llm.initialize(
            checkpoint_dir=str(ckpt), lm_model_path='acestep-5Hz-lm-0.6B', backend='pt',
            device='cuda', offload_to_cpu=True,
        )

    config = GenerationConfig(batch_size=1, use_random_seed=True, audio_format='wav')
    for estilo, salida in trabajos:
        params = GenerationParams(
            caption=estilo['caption'], lyrics='[Instrumental]', instrumental=True,
            bpm=estilo['bpm'], keyscale=estilo['tono'], timesignature=estilo['compas'],
            duration=a.duracion, thinking=not a.sin_lm,
        )
        r = generate_music(dit, llm, params, config, save_dir=str(salida.parent))
        if not r.success:
            print(f'ACE-Step falló en {salida.name}: {r.error}')
            continue
        Path(r.audios[0]['path']).replace(salida)
        quedan = recortar_silencio(salida)
        print(f'{salida} ({quedan:.1f} s tras recortar el silencio; {estilo["tono"]}, {estilo["bpm"]} BPM)')


def descargar_heartmula() -> None:
    from huggingface_hub import snapshot_download

    for repo, sub in [
        ('HeartMuLa/HeartMuLaGen', ''),
        ('HeartMuLa/HeartMuLa-oss-3B-happy-new-year', 'HeartMuLa-oss-3B'),
        ('HeartMuLa/HeartCodec-oss-20260123', 'HeartCodec-oss'),
    ]:
        snapshot_download(repo, local_dir=HEART_CKPT / sub)  # reanuda y salta lo ya bajado


def generar_heartmula(trabajos, a) -> None:
    import soundfile as sf
    import torch
    import torchaudio
    from heartlib import HeartMuLaGenPipeline

    # torchaudio 2.10 guarda vía torchcodec, que choca con el CUDA de este torch.
    torchaudio.save = lambda ruta, wav, sr: sf.write(ruta, wav.T.numpy(), sr)
    descargar_heartmula()
    # lazy_load: carga HeartMuLa, la descarga y recién ahí carga el codec (pico ~6 GB).
    pipe = HeartMuLaGenPipeline.from_pretrained(
        str(HEART_CKPT), device={'mula': torch.device('cuda'), 'codec': torch.device('cuda')},
        dtype={'mula': torch.bfloat16, 'codec': torch.float32}, version='3B', lazy_load=True,
    )
    # Con un solo [Instrumental] corta a ~12 s; una sección cada ~20 s lo estira hasta el tope.
    secciones = ['[Intro]'] + ['[Instrumental]'] * max(1, int(a.duracion // 20)) + ['[Outro]']
    # HeartMuLa solo recibe tags: no tiene parámetros de tonalidad, BPM ni compás.
    for estilo, salida in trabajos:
        with torch.no_grad():
            pipe(
                {'lyrics': '\n\n'.join(secciones), 'tags': estilo['tags'] + ',instrumental'},
                max_audio_length_ms=int(a.duracion * 1000), save_path=str(salida),
                topk=50, temperature=1.0, cfg_scale=1.5,
            )
        quedan = recortar_silencio(salida)
        print(f'{salida} ({quedan:.1f} s tras recortar el silencio)')


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--modelo', choices=MODELOS, required=True)
    ap.add_argument(
        '--estilo', nargs='+', default=['lofi-chill'],
        help=f'uno o más: {", ".join(ESTILOS)} o texto libre entre comillas',
    )
    ap.add_argument('--duracion', type=float, default=60, help='segundos antes del recorte (ACE ≤600, HeartMuLa ≤240)')
    ap.add_argument('--tono', help='tonalidad, ej. "C Major", "A Minor" (obligatoria con texto libre)')
    ap.add_argument('--bpm', type=int, help='tempo 30–300 (obligatorio con texto libre)')
    ap.add_argument('--compas', choices=['2', '3', '4', '6'], help='2/4, 3/4, 4/4 o 6/8 (por defecto 4/4)')
    ap.add_argument('--sin-lm', action='store_true', help='ACE-Step sin el planificador LM 0.6B: ~3x más rápido')
    ap.add_argument('--carpeta', type=Path, default=AQUI.parent / 'out' / 'music', help='por defecto out/music/')
    ap.add_argument(
        '--variantes', type=int, default=1,
        help='pistas por estilo (<modelo>-<estilo>-v1.wav ...); la melodía cambia en cada una',
    )
    ap.add_argument(
        '--evaluar', action='store_true',
        help='al final mide con demucs cuánta voz hay en cada pista y marca las que cantan (se quiere solo música)',
    )
    ap.add_argument(
        '--reintentos', type=int, default=0,
        help='con --evaluar: rondas en las que se regeneran solo las pistas con voz',
    )
    a = ap.parse_args()
    if a.reintentos and not a.evaluar:
        ap.error('--reintentos necesita --evaluar')
    if a.evaluar and a.modelo != 'acestep':
        ap.error('--evaluar solo está en el venv de acestep (ahí está demucs)')
    if a.variantes < 1:
        ap.error('--variantes debe ser 1 o más')

    # Validar antes de relanzar en el venv y cargar el modelo.
    trabajos = []
    for valor in a.estilo:
        nombre, estilo = resolver_estilo(valor, a.tono, a.bpm, a.compas)
        for i in range(1, a.variantes + 1):
            sufijo = f'-v{i}' if a.variantes > 1 else ''
            trabajos.append((estilo, (a.carpeta / f'{a.modelo}-{nombre}{sufijo}.wav').resolve()))

    usar_venv(MODELOS[a.modelo])
    a.carpeta.mkdir(parents=True, exist_ok=True)

    generar = generar_heartmula if a.modelo == 'heartmula' else generar_acestep
    generar(trabajos, a)
    if not a.evaluar:
        return

    liberar_gpu()
    pendientes = con_voz([t[1] for t in trabajos])
    for _ in range(a.reintentos):
        if not pendientes:
            break
        print(f'Regenerando {len(pendientes)} pista(s) con voz...', flush=True)
        generar([t for t in trabajos if t[1] in pendientes], a)
        liberar_gpu()
        pendientes = con_voz(pendientes)
    print(f'{len(trabajos) - len(pendientes)}/{len(trabajos)} pistas sin voz')
    if pendientes:
        sys.exit(f'Con voz tras los reintentos: {", ".join(p.name for p in pendientes)}')


if __name__ == '__main__':
    main()

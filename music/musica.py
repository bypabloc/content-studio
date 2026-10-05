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

# caption: descripción libre para ACE-Step. tags: etiquetas cortas para HeartMuLa.
# tono/bpm/compas: metadatos que el LM de ACE-Step respeta en vez de inventarlos.
# Tonalidades estables según la guía oficial (C, G, D, Am, Em); compás '4' = 4/4.
ESTILOS = {
    'lofi-chill': dict(
        caption='lo-fi hip hop, chill, mellow Rhodes piano, dusty vinyl crackle, soft boom bap drums, warm bass, relaxing',
        tags='lofi,hip hop,chill,piano,relaxing', tono='C Major', bpm=80, compas='4',
    ),
    'lofi-jazz': dict(
        caption='jazzy lo-fi, smooth jazz chords, muted trumpet, upright bass, brushed drums, tape saturation, cozy',
        tags='lofi,jazz,chill,trumpet,cozy', tono='D Minor', bpm=85, compas='4',
    ),
    'lofi-lluvia': dict(
        caption='rainy lo-fi, melancholic piano, rain ambience, vinyl noise, slow lazy drums, nostalgic, calm',
        tags='lofi,rain,melancholic,piano,calm', tono='E Minor', bpm=72, compas='4',
    ),
    'lofi-estudio': dict(
        caption='lo-fi study beats, soft guitar, gentle keys, steady laid-back groove, focused, minimal, background music',
        tags='lofi,study,guitar,focus,minimal', tono='G Major', bpm=78, compas='4',
    ),
    'lofi-nocturno': dict(
        caption='late night lo-fi, dreamy synth pads, deep sub bass, slow swing drums, city night atmosphere, ambient',
        tags='lofi,night,dreamy,synth,ambient', tono='A Minor', bpm=70, compas='4',
    ),
    'corporate': dict(
        caption='corporate background music, uplifting, clean electric piano, light plucks, soft claps, optimistic, modern tech',
        tags='corporate,uplifting,piano,positive,background', tono='C Major', bpm=110, compas='4',
    ),
    'future-bass': dict(
        caption='soft future bass, bright supersaw chords, gentle sidechain, airy plucks, positive, polished, background',
        tags='future bass,electronic,bright,positive,soft', tono='G Major', bpm=100, compas='4',
    ),
    'deep-house': dict(
        caption='deep house, warm groove, smooth chords, round bass, crisp hi-hats, elegant, minimal, background',
        tags='deep house,groove,warm,minimal,elegant', tono='A Minor', bpm=120, compas='4',
    ),
    'ambient': dict(
        caption='ambient, evolving soft pads, gentle piano notes, airy textures, calm, spacious, no drums',
        tags='ambient,calm,pads,piano,spacious', tono='D Major', bpm=70, compas='4',
    ),
}
SILENCIO_DB = -50  # por debajo de esto, la cola final se considera silencio y se recorta


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
    a = ap.parse_args()

    # Validar antes de relanzar en el venv y cargar el modelo.
    trabajos = []
    for valor in a.estilo:
        nombre, estilo = resolver_estilo(valor, a.tono, a.bpm, a.compas)
        trabajos.append((estilo, (a.carpeta / f'{a.modelo}-{nombre}.wav').resolve()))

    usar_venv(MODELOS[a.modelo])
    a.carpeta.mkdir(parents=True, exist_ok=True)

    generar = generar_heartmula if a.modelo == 'heartmula' else generar_acestep
    generar(trabajos, a)


if __name__ == '__main__':
    main()

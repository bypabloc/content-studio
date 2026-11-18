r"""Catálogo de voces libres para narrar sin grabarse: construye y aprueba cada voz.

Uso:
    python narration/voces.py --listar                 # catálogo, licencia y estado de cada voz
    python narration/voces.py --construir yesid        # descarga, genera los 12 estilos y los aprueba
    python narration/voces.py --construir todas --forzar

Cada voz del catálogo (narration/voces/catalogo.json) parte de un clip real de 8-12 s (o de varios clips cortos
del mismo hablante, unidos) con licencia de uso comercial: CC0 o dominio público, o una que pide MENCIÓN
(CC BY, CC BY-SA, Jenny). Mención = atribución: al publicar algo hecho con esa voz hay que dar crédito a su
autor, con el texto `atribucion` del catálogo (mencion(); docs/research/voces-libres-clonacion/12).
Ese clip, normalizado, es el estilo `neutral`. El resto de ESTILOS se genera con CosyVoice 3
(la misma voz leyendo el texto del kit de grabación, dirigido con una instrucción en inglés) y cada clip se
aprueba si conserva la voz (similitud de hablante con la base), se entiende (WER con whisper) y cumple los
criterios de referencia de docs/guiones/README.md. Una voz entra en `tts.py --voz` solo si aprueba TODOS los
estilos. Resultado: narration/voces/<voz>/<estilo>.wav + .txt y aprobacion.json (gitignoreados).
Investigación y mediciones: docs/research/voces-libres-clonacion/.
"""

import argparse
import io
import json
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
VOCES = AQUI / 'voces'
CATALOGO = VOCES / 'catalogo.json'
VOZ_PROPIA = AQUI / 'voz'  # textos del kit de grabación en español (<estilo>.txt)
UA = {'User-Agent': 'content-studio-voces'}
PAUSA_PARTES = 0.4  # s entre las partes de una base armada con varios clips

# Criterios de aprobación de cada clip generado, calibrados en docs/research/voces-libres-clonacion/10.
SIM_MIN = 0.93       # coseno WavLM-SV con la base: instruct2 dio 0.96-0.99; voces ajenas del banco, 0.75-0.95
WER_MAX = 0.15       # palabras mal oídas por whisper sobre el texto pedido
DURACION = (5.0, 15.0)  # los textos de intima y susurro salen en 5-7 s; CosyVoice rechaza > 30 s
RONDAS = 3           # semillas por estilo antes de darlo por reprobado
SEMILLA = 1234
WHISPER = 'large-v3-turbo'

# Instrucción de CosyVoice 3 por estilo (en inglés: en español se leen). None: el estilo sale sin instrucción.
INSTRUCCION = {
    'amistosa': 'Please speak in a friendly, warm and cheerful tone.',
    'suave': 'Please speak in a soft and gentle voice.',
    'experta': 'Please speak in a confident and professional tone.',
    'clara': 'Please speak slowly and clearly.',
    'estable': 'Please speak in a calm and steady tone.',
    'neutral': None,
    'energica': 'Please speak in a cheerful and energetic tone.',
    'dramatica': 'Please speak in a dramatic, suspenseful storytelling tone.',
    'triste': 'Please speak in a sad and slow tone.',
    'intima': 'Please speak in a very soft voice.',
    'susurro': 'Please say it whispering.',
    'neutral-en': None,
}
# Textos del kit para las voces en inglés (las voces en español usan narration/voz/<estilo>.txt).
TEXTO_EN = {
    'amistosa': "Hi, how are you? We've got news that makes us really happy: now you can create your videos in "
                'minutes, right from your phone, with no hassle. Try it today.',
    'suave': 'Breathe calmly. This space was made for you: your ideas, your projects and your notes, all in order '
             'and just one click away.',
    'experta': "Look, the real problem isn't the camera: it's the lack of a clear idea. When the script, the music "
               'and the edit all tell the same story, the video works.',
    'clara': 'To begin, open the main panel. Then select New record, fill in the required fields and save your '
             'changes. The system will confirm it right away.',
    'estable': 'This is a content management platform for creators and small teams. It brings scripts, recording, '
               'editing and publishing together in one place, with secure access from any device.',
    'energica': "It's finally here! Thirty percent off, this weekend only. Jump in now, pick your plan and start "
                'today.',
    'dramatica': 'Nobody knew what had happened that night. The door was open… and on the floor, an unsigned '
                 'letter. That is where it all began.',
    'triste': 'Some days everything weighs a little more. That year we lost so much… and still, we learned to keep '
              'going, together.',
    'intima': "I'm going to tell you something almost nobody knows. Come a little closer… because this changes the "
              'way you see it.',
    'susurro': "I'm going to tell you something almost nobody knows. Come a little closer… because this changes the "
               'way you see it.',
}


def catalogo() -> dict:
    return json.loads(CATALOGO.read_text(encoding='utf-8'))


def aprobadas(estilos) -> dict[str, dict]:
    """Voces del catálogo construidas y aprobadas en todos los `estilos`: {nombre: ficha del catálogo}."""
    out = {}
    for nombre, ficha in catalogo().items():
        ap = VOCES / nombre / 'aprobacion.json'
        if not ap.exists():
            continue
        res = json.loads(ap.read_text(encoding='utf-8'))['estilos']
        if all(res.get(e, {}).get('ok') and (VOCES / nombre / f'{e}.wav').exists() for e in estilos):
            out[nombre] = ficha
    return out


def mencion(ficha: dict) -> str | None:
    """Texto de crédito que hay que publicar con la narración (descripción del video), o None si la licencia no lo pide.

    >>> mencion({'licencia': 'CC0'}) is None
    True
    >>> mencion({'licencia': 'CC BY 4.0', 'atribucion': 'Voz: X, CC BY 4.0'})
    'Voz: X, CC BY 4.0'
    """
    return ficha.get('atribucion')


def estado(nombre: str, estilos) -> str:
    """Texto corto para menús: aprobada, reprobada (cuántos estilos) o sin construir.

    >>> estado('no-existe', ['neutral'])
    'sin construir'
    """
    ap = VOCES / nombre / 'aprobacion.json'
    if not ap.exists():
        return 'sin construir'
    res = json.loads(ap.read_text(encoding='utf-8'))['estilos']
    malos = [e for e in estilos if not res.get(e, {}).get('ok')]
    return 'aprobada' if not malos else f'reprobada en {len(malos)}/{len(estilos)} estilos ({", ".join(malos)})'


def texto_estilo(estilo: str, idioma: str) -> str:
    if estilo == 'neutral-en':
        return (VOZ_PROPIA / 'neutral-en.txt').read_text(encoding='utf-8').strip()
    if idioma == 'en':
        return TEXTO_EN[estilo]
    return (VOZ_PROPIA / f'{estilo}.txt').read_text(encoding='utf-8').strip()


class ZipRemoto(io.RawIOBase):
    """Archivo HTTP de solo lectura con `Range`: zipfile lee el índice y los miembros pedidos, no el zip entero
    (los de OpenSLR pesan ~0.8 GB y cada clip ~1 MB)."""

    def __init__(self, url: str):
        self.url, self.pos = url, 0
        with urllib.request.urlopen(urllib.request.Request(url, method='HEAD', headers=UA)) as r:
            self.size = int(r.headers['Content-Length'])

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = {0: off, 1: self.pos + off, 2: self.size + off}[whence]
        return self.pos

    def readinto(self, b):
        if self.pos >= self.size:
            return 0
        fin = min(self.pos + len(b), self.size) - 1
        with urllib.request.urlopen(urllib.request.Request(self.url, headers={**UA, 'Range': f'bytes={self.pos}-{fin}'})) as r:
            data = r.read()
        b[:len(data)] = data
        self.pos += len(data)
        return len(data)


def bajar(url: str, miembro: str | None = None) -> Path:
    """Archivo de la fuente en la caché narration/voces/.fuentes: la URL entera o, con `miembro`, ese archivo de un zip."""
    cache = VOCES / '.fuentes' / (miembro or url.rsplit('/', 1)[-1].replace('%28', '(').replace('%29', ')'))
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        print(f'Descargando {url}' + (f' → {miembro}' if miembro else ''))
        if miembro:
            with zipfile.ZipFile(io.BufferedReader(ZipRemoto(url), 1 << 16)) as z:
                nombre = next(n for n in z.namelist() if n.endswith('/' + miembro) or n == miembro)
                cache.write_bytes(z.read(nombre))
        else:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA)) as r, open(cache, 'wb') as f:
                shutil.copyfileobj(r, f)
    return cache


def tramo_voz(clip: Path) -> tuple[float, float | None]:
    """(inicio, fin) de la voz en un clip corto: del fin del silencio inicial al primer silencio de 0.8 s o más.
    silenceremove no sirve en los clips de OpenSLR: un clic o una respiración al final frena el recorte."""
    err = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(clip), '-af', 'silencedetect=n=-40dB:d=0.3', '-f', 'null',
                          '-'], capture_output=True, text=True).stderr
    return tramo_de_silencios([float(x) for x in re.findall(r'silence_start: ([\d.]+)', err)],
                              [float(x) for x in re.findall(r'silence_end: ([\d.]+)', err)])


def tramo_de_silencios(ini: list[float], fin: list[float]) -> tuple[float, float | None]:
    """Con los silencios de silencedetect, el tramo con voz (0.08 s antes y 0.12 s después de margen).

    >>> tramo_de_silencios([0.0, 4.1], [1.5, 6.0])     # silencio inicial de 1.5 s, voz hasta 4.1 s
    (1.42, 4.22)
    >>> tramo_de_silencios([0.0, 2.0, 3.0], [1.0, 2.4]) # la pausa de 0.4 s no corta; la que empieza en 3.0 sí
    (0.92, 3.12)
    >>> tramo_de_silencios([], [])                      # sin silencios: el clip entero
    (0.0, None)
    """
    a = fin[0] if ini and ini[0] < 0.05 else 0.0
    b = next((s for s, e in zip(ini, fin + [1e9]) if s > a and e - s >= 0.8), None)
    return round(max(a - 0.08, 0.0), 3), round(b + 0.12, 3) if b else None


def descargar(ficha: dict, destino: Path) -> None:
    """La base cruda de la voz, sin procesar: el tramo `inicio_s`/`dur_s` de `url`, o las `partes` (clips cortos del
    mismo hablante, p. ej. de OpenSLR) sin el silencio de los bordes y unidas con PAUSA_PARTES s entre ellas."""
    mono = ['-ac', '1', '-c:a', 'pcm_s24le']
    if 'partes' not in ficha:
        corte = ['-ss', str(ficha['inicio_s']), '-t', str(ficha['dur_s'])] if 'inicio_s' in ficha else []
        subprocess.run(['ffmpeg', '-v', 'error', '-y', *corte, '-i', str(bajar(ficha['url'])), *mono, str(destino)],
                       check=True)
        return
    clips = [bajar(p['url'], p.get('miembro')) for p in ficha['partes']]
    filtros = []
    for i, c in enumerate(clips):
        a, b = tramo_voz(c)
        filtros.append(f'[{i}]aformat=channel_layouts=mono,atrim=start={a:.3f}' + (f':end={b:.3f}' if b else '')
                       + ',asetpts=N/SR/TB' + (f',apad=pad_dur={PAUSA_PARTES}' if i < len(clips) - 1 else '') + f'[c{i}]')
    union = ''.join(f'[c{i}]' for i in range(len(clips))) + f'concat=n={len(clips)}:v=0:a=1'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *[a for c in clips for a in ('-i', str(c))],
                    '-filter_complex', ';'.join(filtros) + ';' + union, *mono, str(destino)], check=True)


def construir(nombre: str, ficha: dict, forzar: bool) -> bool:
    import numpy as np
    import soundfile as sf
    import torch
    import whisper
    from transformers import AutoFeatureExtractor, WavLMForXVector

    import tts
    from referencia import procesar, verificar

    carpeta = VOCES / nombre
    carpeta.mkdir(parents=True, exist_ok=True)
    idioma = ficha['idioma']
    base = carpeta / 'neutral.wav'
    previo = carpeta / 'aprobacion.json'
    nueva_base = forzar or not base.exists()
    if nueva_base:
        crudo = carpeta / 'base-cruda.wav'
        descargar(ficha, crudo)
        procesar(crudo, base)
        crudo.unlink()
    (carpeta / 'neutral.txt').write_text(ficha['texto'], encoding='utf-8')

    # Con una base nueva, lo aprobado antes (contra la base vieja) ya no vale.
    res = {} if nueva_base or not previo.exists() else json.loads(previo.read_text(encoding='utf-8'))['estilos']
    # Se regenera lo que falta o no aprobó; lo aprobado se conserva.
    pendientes = [e for e in tts.ESTILOS if e != 'neutral'
                  and not ((carpeta / f'{e}.wav').exists() and res.get(e, {}).get('ok'))]
    if idioma == 'en' and 'neutral-en' in pendientes:  # en una voz inglesa, neutral-en es la propia base
        shutil.copy(base, carpeta / 'neutral-en.wav')
        (carpeta / 'neutral-en.txt').write_text(ficha['texto'], encoding='utf-8')
        pendientes.remove('neutral-en')
        res.pop('neutral-en', None)
    for e in pendientes:
        res.pop(e, None)

    m = tts.MOTORES['cosyvoice3']
    sys_ = tts.SYS_COSYVOICE

    def guardar():
        """aprobacion.json tras cada ronda, de forma atómica: un corte no deja un JSON a medias."""
        ok = all(res.get(e, {}).get('ok') for e in tts.ESTILOS)
        tmp = previo.with_suffix('.tmp')
        tmp.write_text(json.dumps(dict(voz=nombre, aprobada=ok, licencia_motor=m['licencia'],
                                       criterios=dict(sim_min=SIM_MIN, wer_max=WER_MAX, duracion=DURACION),
                                       estilos=res), ensure_ascii=False, indent=1), encoding='utf-8')
        tmp.replace(previo)
        return ok
    asr = sv = fe = None

    @torch.no_grad()
    def emb(path):
        import librosa
        y, _ = librosa.load(str(path), sr=16000, mono=True)
        x = fe(y, sampling_rate=16000, return_tensors='pt').to('cuda')
        return torch.nn.functional.normalize(sv(**x).embeddings, dim=-1)[0].cpu()

    def evaluar(e, wav):
        nonlocal asr, sv, fe
        if asr is None:
            asr = whisper.load_model(WHISPER, device='cuda')
            fe = AutoFeatureExtractor.from_pretrained('microsoft/wavlm-base-plus-sv')
            sv = WavLMForXVector.from_pretrained('microsoft/wavlm-base-plus-sv').to('cuda').eval()
        lengua = 'en' if e == 'neutral-en' else idioma
        oido = asr.transcribe(str(wav), language=lengua, condition_on_previous_text=False)['text']
        esperado = tts.normalizar(wav.with_suffix('.txt').read_text(encoding='utf-8'), lengua)
        difs = tts.comparar(esperado, tts.normalizar(oido, lengua))
        wer = sum(max(len(a.split()), len(b.split())) for _, a, b in difs) / max(len(esperado), 1)
        sim = float(emb(wav) @ emb(base))
        checks = verificar(wav, *DURACION, piso=False)
        checks += [(sim >= SIM_MIN, f'similitud con la base {sim:.3f} (mínimo {SIM_MIN})'),
                   (wer <= WER_MAX, f'WER {wer:.2f} (máximo {WER_MAX}): oyó "{oido.strip()}"')]
        return dict(ok=all(c for c, _ in checks), sim=round(sim, 3), wer=round(wer, 3),
                    checks=[t for c, t in checks if not c])

    # Un modelo a la vez en la GPU: con whisper y WavLM cargados, CosyVoice desborda los 8 GB y va ~15× más lento.
    for ronda in range(RONDAS):
        faltan = [e for e in pendientes if not res.get(e, {}).get('ok')]
        if not faltan:
            break
        asr = sv = fe = None
        tts.liberar()
        modelo = tts.cargar_cosyvoice(m['codigo'], m['repo'])
        crudos = {}
        for e in faltan:
            tts.fijar(SEMILLA + ronda)
            texto = texto_estilo(e, idioma)
            # neutral-en de una voz en español: zero-shot con la transcripción en español. inference_cross_lingual
            # pierde la voz (SIM 0.71-0.91 con la base, a veces más cerca de una voz inglesa); ver research/…/10 §6.
            if INSTRUCCION[e] is None:
                partes = modelo.inference_zero_shot(texto, f'{sys_}<|endofprompt|>{ficha["texto"]}', str(base),
                                                    stream=False, text_frontend=False)
            else:
                partes = modelo.inference_instruct2(texto, f'{sys_} {INSTRUCCION[e]}<|endofprompt|>', str(base),
                                                    stream=False, text_frontend=False)
            audio = torch.cat([j['tts_speech'] for j in partes], dim=1).squeeze(0).cpu().numpy()
            crudos[e] = carpeta / f'{e}.crudo.wav'
            sf.write(str(crudos[e]), audio.astype(np.float32), modelo.sample_rate)
        del modelo
        tts.liberar()  # CosyVoice fuera de la VRAM antes de whisper y WavLM
        if 'neutral' not in res:
            res['neutral'] = evaluar('neutral', base)
        for e, crudo in crudos.items():
            final = carpeta / f'{e}.wav'
            procesar(crudo, final)
            crudo.unlink()
            (carpeta / f'{e}.txt').write_text(texto_estilo(e, idioma), encoding='utf-8')
            res[e] = evaluar(e, final) | {'ronda': ronda + 1}
            print(f'  {"OK " if res[e]["ok"] else "NO "} {e:<11} sim {res[e]["sim"]:.3f}  WER {res[e]["wer"]:.2f}'
                  + (f'  ← {"; ".join(res[e]["checks"])}' if res[e]['checks'] else ''), flush=True)
        guardar()
    if 'neutral' not in res:  # nada que generar (todo existía): igual se evalúa la base
        res['neutral'] = evaluar('neutral', base)
    if 'neutral-en' not in res:  # copia de la base en una voz inglesa
        res['neutral-en'] = res['neutral']
    ok = guardar()
    print(f'{nombre}: {"APROBADA" if ok else "REPROBADA"} ({sum(r["ok"] for r in res.values())}/{len(res)} estilos)')
    return ok


def construir_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()  # sin flags (p. ej. desde el menú de cli.py) equivale a --listar
    g.add_argument('--listar', action='store_true', help='muestra el catálogo y el estado de cada voz (por defecto)')
    g.add_argument('--construir', nargs='+', metavar='VOZ', help='voces a construir y aprobar, o "todas"')
    ap.add_argument('--forzar', action='store_true', help='regenera todo aunque ya exista')
    return ap


def main() -> None:
    a = construir_parser().parse_args()
    sys.path.insert(0, str(AQUI))
    import tts

    cat = catalogo()
    if not a.construir:
        for nombre, f in cat.items():
            print(f'{nombre:<16} {f["idioma"]} · {f["licencia"]} · {f["descripcion"]}\n{"":<16} {estado(nombre, tts.ESTILOS)}')
            if m := mencion(f):
                print(f'{"":<16} mención obligatoria: {m}')
        return
    nombres = list(cat) if a.construir == ['todas'] else a.construir
    if desconocidas := [n for n in nombres if n not in cat]:
        sys.exit(f'Voz desconocida: {", ".join(desconocidas)}. Opciones: {", ".join(cat)}')
    tts.usar_venv(tts.MOTORES['cosyvoice3']['venv'], __file__)  # relanza este script en el venv de CosyVoice
    print(f'Aviso: los estilos se generan con CosyVoice 3 ({tts.MOTORES["cosyvoice3"]["licencia"]}). '
          'Ver docs/research/voces-libres-clonacion/02.')
    resultados = {n: construir(n, cat[n], a.forzar) for n in nombres}
    sys.exit(0 if all(resultados.values()) else 1)


if __name__ == '__main__':
    main()

"""Construye una voz del catálogo: la base es el clip real; el resto de los estilos se genera con CosyVoice 3 y se
aprueba con similitud de hablante (WavLM), WER (whisper) y los criterios de referencia. Corre en el venv de CosyVoice:
torch, whisper y transformers se importan dentro de construir()."""

from __future__ import annotations

import json
import shutil

from content_studio.narration.estilos import ESTILOS
from content_studio.narration.motores.registro import MOTORES, liberar_todo
from content_studio.narration.referencia import procesar, verificar
from content_studio.narration.voces.fuentes import descargar
from content_studio.rutas import VOCES, VOZ

# Criterios de aprobación de cada clip generado, calibrados en docs/research/voces-libres-clonacion/10.
SIM_MIN = 0.93  # coseno WavLM-SV con la base: instruct2 dio 0.96-0.99; voces ajenas del banco, 0.75-0.95
WER_MAX = 0.15  # palabras mal oídas por whisper sobre el texto pedido
DURACION = (5.0, 15.0)  # los textos de intima y susurro salen en 5-7 s; CosyVoice rechaza > 30 s
RONDAS = 3  # semillas por estilo antes de darlo por reprobado
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


def texto_estilo(estilo: str, idioma: str) -> str:
    if estilo == 'neutral-en':
        return (VOZ / 'neutral-en.txt').read_text(encoding='utf-8').strip()
    if idioma == 'en':
        return TEXTO_EN[estilo]
    return (VOZ / f'{estilo}.txt').read_text(encoding='utf-8').strip()


def construir(nombre: str, ficha: dict, forzar: bool) -> bool:
    import numpy as np
    import soundfile as sf
    import torch
    import whisper
    from transformers import AutoFeatureExtractor, WavLMForXVector

    from content_studio.narration.evaluacion.comparar import comparar, normalizar
    from content_studio.narration.motores.cosyvoice import SISTEMA as sys_
    from content_studio.narration.motores.cosyvoice import cargar as cargar_cosyvoice
    from content_studio.narration.pipeline import fijar

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
    pendientes = [
        e for e in ESTILOS if e != 'neutral' and not ((carpeta / f'{e}.wav').exists() and res.get(e, {}).get('ok'))
    ]
    if idioma == 'en' and 'neutral-en' in pendientes:  # en una voz inglesa, neutral-en es la propia base
        shutil.copy(base, carpeta / 'neutral-en.wav')
        (carpeta / 'neutral-en.txt').write_text(ficha['texto'], encoding='utf-8')
        pendientes.remove('neutral-en')
        res.pop('neutral-en', None)
    for e in pendientes:
        res.pop(e, None)

    m = MOTORES['cosyvoice3']

    def guardar():
        """aprobacion.json tras cada ronda, de forma atómica: un corte no deja un JSON a medias."""
        ok = all(res.get(e, {}).get('ok') for e in ESTILOS)
        criterios = dict(sim_min=SIM_MIN, wer_max=WER_MAX, duracion=DURACION)
        datos = dict(voz=nombre, aprobada=ok, licencia_motor=m.licencia, criterios=criterios, estilos=res)
        tmp = previo.with_suffix('.tmp')
        tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding='utf-8')
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
        esperado = normalizar(wav.with_suffix('.txt').read_text(encoding='utf-8'), lengua)
        difs = comparar(esperado, normalizar(oido, lengua))
        wer = sum(max(len(a.split()), len(b.split())) for _, a, b in difs) / max(len(esperado), 1)
        sim = float(emb(wav) @ emb(base))
        checks = verificar(wav, *DURACION, piso=False)
        checks += [
            (sim >= SIM_MIN, f'similitud con la base {sim:.3f} (mínimo {SIM_MIN})'),
            (wer <= WER_MAX, f'WER {wer:.2f} (máximo {WER_MAX}): oyó "{oido.strip()}"'),
        ]
        return dict(
            ok=all(c for c, _ in checks), sim=round(sim, 3), wer=round(wer, 3), checks=[t for c, t in checks if not c]
        )

    # Un modelo a la vez en la GPU: con whisper y WavLM cargados, CosyVoice desborda los 8 GB y va ~15× más lento.
    for ronda in range(RONDAS):
        faltan = [e for e in pendientes if not res.get(e, {}).get('ok')]
        if not faltan:
            break
        asr = sv = fe = None
        liberar_todo()
        modelo = cargar_cosyvoice(m.codigo, m.repo)
        crudos = {}
        for e in faltan:
            fijar(SEMILLA + ronda)
            texto = texto_estilo(e, idioma)
            # neutral-en de una voz en español: zero-shot con la transcripción en español. inference_cross_lingual
            # pierde la voz (SIM 0.71-0.91 con la base, a veces más cerca de una voz inglesa); ver research/…/10 §6.
            if INSTRUCCION[e] is None:
                partes = modelo.inference_zero_shot(
                    texto, f'{sys_}<|endofprompt|>{ficha["texto"]}', str(base), stream=False, text_frontend=False
                )
            else:
                partes = modelo.inference_instruct2(
                    texto, f'{sys_} {INSTRUCCION[e]}<|endofprompt|>', str(base), stream=False, text_frontend=False
                )
            audio = torch.cat([j['tts_speech'] for j in partes], dim=1).squeeze(0).cpu().numpy()
            crudos[e] = carpeta / f'{e}.crudo.wav'
            sf.write(str(crudos[e]), audio.astype(np.float32), modelo.sample_rate)
        del modelo
        liberar_todo()  # CosyVoice fuera de la VRAM antes de whisper y WavLM
        if 'neutral' not in res:
            res['neutral'] = evaluar('neutral', base)
        for e, crudo in crudos.items():
            final = carpeta / f'{e}.wav'
            procesar(crudo, final)
            crudo.unlink()
            (carpeta / f'{e}.txt').write_text(texto_estilo(e, idioma), encoding='utf-8')
            res[e] = evaluar(e, final) | {'ronda': ronda + 1}
            print(
                f'  {"OK " if res[e]["ok"] else "NO "} {e:<11} sim {res[e]["sim"]:.3f}  WER {res[e]["wer"]:.2f}'
                + (f'  ← {"; ".join(res[e]["checks"])}' if res[e]['checks'] else ''),
                flush=True,
            )
        guardar()
    if 'neutral' not in res:  # nada que generar (todo existía): igual se evalúa la base
        res['neutral'] = evaluar('neutral', base)
    if 'neutral-en' not in res:  # copia de la base en una voz inglesa
        res['neutral-en'] = res['neutral']
    ok = guardar()
    print(f'{nombre}: {"APROBADA" if ok else "REPROBADA"} ({sum(r["ok"] for r in res.values())}/{len(res)} estilos)')
    return ok

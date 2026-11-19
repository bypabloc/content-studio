"""Construye una voz del catálogo: la base es el clip real; el resto de los estilos se genera con CosyVoice 3 y se
aprueba con similitud de hablante (WavLM), WER (whisper) y los criterios de referencia. Corre en el venv de CosyVoice:
torch, whisper y transformers se importan dentro de construir()."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from content_studio.narration.engines.registry import ENGINES, free_todo
from content_studio.narration.reference import process, verify
from content_studio.narration.styles import STYLES
from content_studio.narration.voices.sources import download
from content_studio.paths import REFERENCE, VOICES

# Criterios de aprobación de cada clip generado, calibrados en docs/research/voces-libres-clonacion/10.
SIM_MIN = 0.93  # coseno WavLM-SV con la base: instruct2 dio 0.96-0.99; voces ajenas del banco, 0.75-0.95
WER_MAX = 0.15  # palabras mal oídas por whisper sobre el texto pedido
DURATION = (5.0, 15.0)  # los textos de intima y susurro salen en 5-7 s; CosyVoice rechaza > 30 s
ROUNDS = 3  # semillas por estilo antes de darlo por reprobado
SEED = 1234
WHISPER = 'large-v3-turbo'

# Instrucción de CosyVoice 3 por estilo (en inglés: en español se leen). None: el estilo sale sin instrucción.
INSTRUCTION = {
    'friendly': 'Please speak in a friendly, warm and cheerful tone.',
    'soft': 'Please speak in a soft and gentle voice.',
    'expert': 'Please speak in a confident and professional tone.',
    'clear': 'Please speak slowly and clearly.',
    'steady': 'Please speak in a calm and steady tone.',
    'neutral': None,
    'energetic': 'Please speak in a cheerful and energetic tone.',
    'dramatic': 'Please speak in a dramatic, suspenseful storytelling tone.',
    'sad': 'Please speak in a sad and slow tone.',
    'intimate': 'Please speak in a very soft voice.',
    'whisper': 'Please say it whispering.',
    'neutral-en': None,
}
# Textos del kit para las voces en inglés (las voces en español usan server/data/narration/reference/<estilo>.txt).
TEXT_EN = {
    'friendly': "Hi, how are you? We've got news that makes us really happy: now you can create your videos in "
    'minutes, right from your phone, with no hassle. Try it today.',
    'soft': 'Breathe calmly. This space was made for you: your ideas, your projects and your notes, all in order '
    'and just one click away.',
    'expert': "Look, the real problem isn't the camera: it's the lack of a clear idea. When the script, the music "
    'and the edit all tell the same story, the video works.',
    'clear': 'To begin, open the main panel. Then select New record, fill in the required fields and save your '
    'changes. The system will confirm it right away.',
    'steady': 'This is a content management platform for creators and small teams. It brings scripts, recording, '
    'editing and publishing together in one place, with secure access from any device.',
    'energetic': "It's finally here! Thirty percent off, this weekend only. Jump in now, pick your plan and start "
    'today.',
    'dramatic': 'Nobody knew what had happened that night. The door was open… and on the floor, an unsigned '
    'letter. That is where it all began.',
    'sad': 'Some days everything weighs a little more. That year we lost so much… and still, we learned to keep '
    'going, together.',
    'intimate': "I'm going to tell you something almost nobody knows. Come a little closer… because this changes the "
    'way you see it.',
    'whisper': "I'm going to tell you something almost nobody knows. Come a little closer… because this changes the "
    'way you see it.',
}


def text_style(style: str, language: str) -> str:
    """Texto de prueba de un estilo en el idioma indicado."""
    if style == 'neutral-en':
        return (REFERENCE / 'neutral-en.txt').read_text(encoding='utf-8').strip()
    if language == 'en':
        return TEXT_EN[style]
    return (REFERENCE / f'{style}.txt').read_text(encoding='utf-8').strip()


def build(name: str, sheet: dict, force: bool) -> bool:
    """Construye una voz de referencia, la evalúa y la aprueba; True si pasó."""
    import numpy as np
    import soundfile as sf
    import torch
    import whisper
    from transformers import AutoFeatureExtractor, WavLMForXVector

    from content_studio.narration.engines.cosyvoice import SYSTEM as sys_
    from content_studio.narration.engines.cosyvoice import load as load_cosyvoice
    from content_studio.narration.evaluation.compare import compare, normalize
    from content_studio.narration.pipeline import fix

    folder = VOICES / name
    folder.mkdir(parents=True, exist_ok=True)
    language = sheet['language']
    base = folder / 'neutral.wav'
    # cspell:ignore aprobacion
    # aprobacion.json: nombre en disco de las voces construidas (move-data no lo cambia, ver WARNING 002).
    previous = folder / 'aprobacion.json'
    new_base = force or not base.exists()
    if new_base:
        raw = folder / 'base-raw.wav'
        download(sheet, raw)
        process(raw, base)
        raw.unlink()
    (folder / 'neutral.txt').write_text(sheet['text'], encoding='utf-8')

    # Con una base nueva, lo aprobado antes (contra la base vieja) ya no vale.
    res = {} if new_base or not previous.exists() else json.loads(previous.read_text(encoding='utf-8'))['styles']
    # Se regenera lo que falta o no aprobó; lo aprobado se conserva.
    pending = [
        e for e in STYLES if e != 'neutral' and not ((folder / f'{e}.wav').exists() and res.get(e, {}).get('ok'))
    ]
    if language == 'en' and 'neutral-en' in pending:  # en una voz inglesa, neutral-en es la propia base
        shutil.copy(base, folder / 'neutral-en.wav')
        (folder / 'neutral-en.txt').write_text(sheet['text'], encoding='utf-8')
        pending.remove('neutral-en')
        res.pop('neutral-en', None)
    for e in pending:
        res.pop(e, None)

    m = ENGINES['cosyvoice3']

    def save():
        """aprobacion.json tras cada ronda, de forma atómica: un corte no deja un JSON a medias."""
        ok = all(res.get(e, {}).get('ok') for e in STYLES)
        criteria = dict(sim_min=SIM_MIN, wer_max=WER_MAX, duration=DURATION)
        data = dict(voice=name, approved=ok, license_engine=m.license, criteria=criteria, styles=res)
        tmp = previous.with_suffix('.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
        tmp.replace(previous)
        return ok

    asr = sv = fe = None

    @torch.no_grad()
    def emb(path: Path) -> torch.Tensor:
        import librosa

        y, _ = librosa.load(str(path), sr=16000, mono=True)
        x = fe(y, sampling_rate=16000, return_tensors='pt').to('cuda')
        return torch.nn.functional.normalize(sv(**x).embeddings, dim=-1)[0].cpu()

    def evaluate(e: str, wav: Path) -> dict:
        nonlocal asr, sv, fe
        if asr is None:
            asr = whisper.load_model(WHISPER, device='cuda')
            fe = AutoFeatureExtractor.from_pretrained('microsoft/wavlm-base-plus-sv')
            sv = WavLMForXVector.from_pretrained('microsoft/wavlm-base-plus-sv').to('cuda').eval()
        lang = 'en' if e == 'neutral-en' else language
        hearing = asr.transcribe(str(wav), language=lang, condition_on_previous_text=False)['text']
        expected = normalize(wav.with_suffix('.txt').read_text(encoding='utf-8'), lang)
        diffs = compare(expected, normalize(hearing, lang))
        wer = sum(max(len(a.split()), len(b.split())) for _, a, b in diffs) / max(len(expected), 1)
        sim = float(emb(wav) @ emb(base))
        checks = verify(wav, *DURATION, floor=False)
        checks += [
            (sim >= SIM_MIN, f'similarity to the base {sim:.3f} (minimum {SIM_MIN})'),
            (wer <= WER_MAX, f'WER {wer:.2f} (maximum {WER_MAX}): heard "{hearing.strip()}"'),
        ]
        return dict(
            ok=all(c for c, _ in checks), sim=round(sim, 3), wer=round(wer, 3), checks=[t for c, t in checks if not c]
        )

    # Un modelo a la vez en la GPU: con whisper y WavLM cargados, CosyVoice desborda los 8 GB y va ~15× más lento.
    for attempt in range(ROUNDS):
        missing = [e for e in pending if not res.get(e, {}).get('ok')]
        if not missing:
            break
        asr = sv = fe = None
        free_todo()
        model = load_cosyvoice(m.code, m.repo)
        raws = {}
        for e in missing:
            fix(SEED + attempt)
            text = text_style(e, language)
            # neutral-en de una voz en español: zero-shot con la transcripción en español. inference_cross_lingual
            # pierde la voz (SIM 0.71-0.91 con la base, a veces más cerca de una voz inglesa); ver research/…/10 §6.
            if INSTRUCTION[e] is None:
                parts = model.inference_zero_shot(
                    text, f'{sys_}<|endofprompt|>{sheet["text"]}', str(base), stream=False, text_frontend=False
                )
            else:
                parts = model.inference_instruct2(
                    text, f'{sys_} {INSTRUCTION[e]}<|endofprompt|>', str(base), stream=False, text_frontend=False
                )
            audio = torch.cat([j['tts_speech'] for j in parts], dim=1).squeeze(0).cpu().numpy()
            raws[e] = folder / f'{e}.raw.wav'
            sf.write(str(raws[e]), audio.astype(np.float32), model.sample_rate)
        del model
        free_todo()  # CosyVoice fuera de la VRAM antes de whisper y WavLM
        if 'neutral' not in res:
            res['neutral'] = evaluate('neutral', base)
        for e, raw in raws.items():
            final = folder / f'{e}.wav'
            process(raw, final)
            raw.unlink()
            (folder / f'{e}.txt').write_text(text_style(e, language), encoding='utf-8')
            res[e] = evaluate(e, final) | {'round': attempt + 1}
            print(
                f'  {"OK " if res[e]["ok"] else "NO "} {e:<11} sim {res[e]["sim"]:.3f}  WER {res[e]["wer"]:.2f}'
                + (f'  ← {"; ".join(res[e]["checks"])}' if res[e]['checks'] else ''),
                flush=True,
            )
        save()
    if 'neutral' not in res:  # nada que generar (todo existía): igual se evalúa la base
        res['neutral'] = evaluate('neutral', base)
    if 'neutral-en' not in res:  # copia de la base en una voz inglesa
        res['neutral-en'] = res['neutral']
    ok = save()
    print(f'{name}: {"APPROVED" if ok else "REJECTED"} ({sum(r["ok"] for r in res.values())}/{len(res)} styles)')
    return ok

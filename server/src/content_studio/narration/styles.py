"""Estilos de narración y emociones del guion (§6.1), con el vector de emoción de IndexTTS (§6.2)."""

from __future__ import annotations

# El estilo sale sobre todo de la referencia grabada en ese tono; estos valores
# solo lo empujan. velocidad se aplica con ffmpeg atempo (no cambia el tono).
STYLES = {
    'friendly': dict(speed=1.05, temperature=0.8, exaggeration=0.6, cfg_weight=0.4),
    'soft': dict(speed=1.0, temperature=0.7, exaggeration=0.4, cfg_weight=0.5),
    'expert': dict(speed=1.0, temperature=0.7, exaggeration=0.5, cfg_weight=0.5),
    'clear': dict(speed=0.97, temperature=0.6, exaggeration=0.35, cfg_weight=0.6),
    'steady': dict(speed=1.05, temperature=0.6, exaggeration=0.3, cfg_weight=0.5),
    'neutral': dict(speed=1.0, temperature=0.7, exaggeration=0.5, cfg_weight=0.5),
    'energetic': dict(speed=1.0, temperature=0.8, exaggeration=0.7, cfg_weight=0.3),
    'dramatic': dict(speed=1.0, temperature=0.7, exaggeration=0.6, cfg_weight=0.3),
    'sad': dict(speed=1.0, temperature=0.7, exaggeration=0.4, cfg_weight=0.5),
    'intimate': dict(speed=1.0, temperature=0.7, exaggeration=0.4, cfg_weight=0.5),
    'whisper': dict(speed=1.0, temperature=0.7, exaggeration=0.3, cfg_weight=0.5),
    'neutral-en': dict(speed=1.0, temperature=0.7, exaggeration=0.5, cfg_weight=0.5),
}

# Emociones (§6.1). vector: índices de IndexTTS [happy, angry, sad, afraid, disgusted, melancholic, surprised, calm].
# voxcpm y cosy: instrucción de VoxCPM2 y de CosyVoice 3. chatterbox: (exaggeration, cfg_weight) a intensidad 0.6.
# ref: estilo de referencia que la representa en Qwen y OmniVoice (None: no hay).
EMOTIONS = {
    'happy': dict(
        vector={0: 0.8},
        voxcpm='cheerful and energetic',
        cosy='Please speak in a cheerful and energetic tone.',
        chatterbox=(0.7, 0.3),
        ref='energetic',
    ),
    'sad': dict(
        vector={2: 0.8},
        voxcpm='sad and slow',
        cosy='Please speak in a sad and slow tone.',
        chatterbox=(0.4, 0.5),
        ref='sad',
    ),
    'angry': dict(
        vector={1: 0.8}, voxcpm='angry and firm', cosy='Please speak in an angry tone.', chatterbox=(0.8, 0.3), ref=None
    ),
    'fear': dict(
        vector={3: 0.8},
        voxcpm='tense and fearful',
        cosy='Please speak in a fearful tone.',
        chatterbox=(0.6, 0.3),
        ref='dramatic',
    ),
    'surprise': dict(
        vector={6: 0.8},
        voxcpm='surprised and amazed',
        cosy='Please speak in a surprised tone.',
        chatterbox=(0.7, 0.3),
        ref='friendly',
    ),
    'calm': dict(
        vector={7: 0.8},
        voxcpm='calm and confident',
        cosy='Please speak in a calm, warm tone.',
        chatterbox=(0.3, 0.5),
        ref='soft',
    ),
    'urgent': dict(
        vector={3: 0.5, 6: 0.3},
        voxcpm='urgent, speaking fast',
        cosy='Please speak in an urgent tone, speaking fast.',
        chatterbox=(0.7, 0.3),
        ref='energetic',
    ),
    'whisper': dict(vector=None, voxcpm='whispering', cosy=None, chatterbox=None, ref='intimate'),
}
# Sesgo del vector de emoción de la WebUI de IndexTTS (§6.2).
BIAS_INDEXTTS = [0.9375, 0.875, 1.0, 1.0, 0.9375, 0.9375, 0.6875, 0.5625]


def normalize_vec(v: list[float]) -> list[float]:
    """Vector de emoción de IndexTTS con el sesgo de su WebUI (§6.2). Si suma más de 0.8, se escala a 0.8.

    >>> [round(x, 3) for x in normalize_vec([0.8, 0, 0, 0, 0, 0, 0, 0])]
    [0.75, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    >>> [round(x, 3) for x in normalize_vec([0, 0, 0, 0.5, 0, 0, 0.3, 0])]
    [0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.206, 0.0]
    >>> round(sum(normalize_vec([0.8] * 8)), 3)
    0.8
    """
    v = [a * b for a, b in zip(v, BIAS_INDEXTTS, strict=False)]
    s = sum(v)
    return [x / s * 0.8 for x in v] if s > 0.8 else v

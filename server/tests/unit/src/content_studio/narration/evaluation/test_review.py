"""--evaluate (spec 013, D-7): cada bloque lo transcribe el servicio de faster-whisper, junto a su audio."""

from __future__ import annotations

import json

from content_studio.narration.evaluation import review


def test_transcribe_leaves_next_to_each_block_the_text_the_service_heard(tmp_path, monkeypatch):
    calls = []

    def heard(path, *, model, language):
        calls.append((path.name, model, language))
        return f'texto de {path.stem}'

    monkeypatch.setattr(review.transcribe_main, 'transcribe_text', heard)
    wavs = [tmp_path / '01.wav', tmp_path / '02.wav']

    review.transcribe(wavs, 'es', 'large-v3-turbo')

    assert json.loads((tmp_path / '02.json').read_text(encoding='utf-8')) == {'text': 'texto de 02'}
    assert calls == [('01.wav', 'large-v3-turbo', 'es'), ('02.wav', 'large-v3-turbo', 'es')]

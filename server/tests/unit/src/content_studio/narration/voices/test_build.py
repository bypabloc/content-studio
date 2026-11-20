"""Textos de prueba de las voces (spec 010, D-1): el texto de cada estilo sale del perfil default, no de la raíz."""

from __future__ import annotations

from content_studio import paths
from content_studio.narration.voices import build


def test_kit_text_comes_from_the_default_profile(tmp_path, monkeypatch):
    refs = tmp_path / 'reference'
    (refs / 'default').mkdir(parents=True)
    (refs / 'default/neutral-en.txt').write_text('Hello there.\n', encoding='utf-8')
    (refs / 'default/clear.txt').write_text('Hola.\n', encoding='utf-8')
    monkeypatch.setattr(paths, 'REFERENCE', refs)

    assert build.text_style('neutral-en', 'en') == 'Hello there.'
    assert build.text_style('clear', 'es') == 'Hola.'

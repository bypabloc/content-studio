"""Catálogo de estilos para la UI (spec 011, D-2 y D-3, AC-4): categoría y si el preset ya tiene su muestra."""

from __future__ import annotations

from content_studio.music.styles import STYLES, styles_catalog


def test_the_catalog_lists_every_preset_with_its_category_and_its_metadata(tmp_path):
    rows = styles_catalog(tmp_path)

    assert len(rows) == len(STYLES) == 126
    first = rows[0]
    assert set(first) == {'key', 'category', 'musical_key', 'bpm', 'time_signature', 'caption', 'has_sample'}
    assert first['key'] == 'lofi-chill' and first['musical_key'] == 'C Major' and first['bpm'] == 80


def test_has_sample_follows_the_files_in_the_samples_folder(tmp_path):
    (tmp_path / 'lofi-chill.wav').write_bytes(b'RIFF')

    rows = {row['key']: row['has_sample'] for row in styles_catalog(tmp_path)}

    assert rows['lofi-chill'] is True
    assert rows['lofi-jazz'] is False

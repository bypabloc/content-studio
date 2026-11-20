"""API de música (spec 011, D-2 y D-3, AC-4): `GET /music/styles` da los 126 presets con su categoría."""

from __future__ import annotations

from content_studio import paths


def test_ac4_get_music_styles_gives_126_presets_each_with_a_category(api, monkeypatch, tmp_path):
    monkeypatch.setattr(paths, 'MUSIC', tmp_path / 'music')
    (tmp_path / 'music' / 'samples').mkdir(parents=True)
    (tmp_path / 'music' / 'samples' / 'lofi-chill.wav').write_bytes(b'RIFF')

    styles = api.client.get('/music/styles', headers=api.headers).json()['styles']

    assert len(styles) == 126
    assert all(row['category'] for row in styles)
    assert {row['key']: row['has_sample'] for row in styles}['lofi-chill'] is True

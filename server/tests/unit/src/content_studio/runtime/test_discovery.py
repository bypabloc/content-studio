"""Spec 028, AC-4: el token de la instalación persiste entre arranques y `--rotate` lo cambia."""

from content_studio.runtime import discovery


def test_ac4_token_persists_and_rotates(tmp_path):
    first = discovery.token(tmp_path)
    assert discovery.token(tmp_path) == first
    assert len(first) == 64
    rotated = discovery.token(tmp_path, rotate=True)
    assert rotated != first
    assert discovery.token(tmp_path) == rotated

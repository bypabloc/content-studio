"""Rutas que la API puede servir (spec 004, D-5; lo usan /files y /media): dentro de out/ o de referencia, o 403."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from content_studio.api.errors import ApiError
from content_studio.api.paths_guard import allowed_file


def request_with(roots: list) -> SimpleNamespace:
    """Un Request con solo lo que mira `allowed_file`: las carpetas permitidas."""
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(roots=roots, dynamic_outputs=False)))


def test_a_file_inside_an_allowed_root_is_returned_resolved(tmp_path):
    root = (tmp_path / 'out').resolve()
    root.mkdir()
    (root / 'a.wav').write_bytes(b'x')

    assert allowed_file(request_with([root]), str(root / 'a.wav')) == root / 'a.wav'


def test_a_path_outside_the_roots_is_403_even_with_dot_dot(tmp_path):
    root = (tmp_path / 'out').resolve()
    root.mkdir()
    (tmp_path / 'secret.wav').write_bytes(b'x')

    with pytest.raises(ApiError) as outside:
        allowed_file(request_with([root]), str(tmp_path / 'secret.wav'))
    with pytest.raises(ApiError) as escape:
        allowed_file(request_with([root]), str(root / '..' / 'secret.wav'))

    assert outside.value.status_code == 403
    assert escape.value.status_code == 403


def test_a_missing_file_inside_the_roots_is_404(tmp_path):
    root = (tmp_path / 'out').resolve()
    root.mkdir()

    with pytest.raises(ApiError) as missing:
        allowed_file(request_with([root]), str(root / 'nope.wav'))

    assert missing.value.status_code == 404

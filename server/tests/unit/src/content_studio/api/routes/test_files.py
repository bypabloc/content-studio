"""Archivos de la API (spec 004, D-5, AC-6): solo dentro de out/ y de los datos de referencia; `..` da 403."""

from __future__ import annotations


def test_ac6_a_path_that_escapes_the_allowed_roots_is_forbidden(api):
    response = api.client.get('/files', params={'path': '../../etc/passwd', 'token': api.token})

    assert response.status_code == 403
    assert response.json()['code'] == 'forbidden_path'


def test_a_file_inside_the_allowed_root_is_served_with_the_query_token(api):
    out = api.tmp / 'out'
    out.mkdir()
    (out / 'a.wav').write_bytes(b'RIFF')

    response = api.client.get('/files', params={'path': str(out / 'a.wav'), 'token': api.token})

    assert response.status_code == 200
    assert response.content == b'RIFF'


def test_a_missing_file_inside_the_root_is_404(api):
    response = api.client.get('/files', params={'path': str(api.tmp / 'out' / 'no.wav'), 'token': api.token})

    assert response.status_code == 404

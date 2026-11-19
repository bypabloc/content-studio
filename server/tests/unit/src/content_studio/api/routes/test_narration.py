"""POST /narration/lint (spec 006, AC-1): incidencias con línea, columna, largo y texto, y la duración."""

from __future__ import annotations


def test_ac1_lint_endpoint_returns_the_issues_with_their_message(api):
    body = api.client.post(
        '/narration/lint', json={'text': 'Hola; esto es DEMO con 24 horas.'}, headers=api.headers
    ).json()

    assert [(i['rule'], i['line'], i['col'], i['length']) for i in body['issues']] == [
        (6, 1, 5, 1),
        (2, 1, 15, 4),
        (13, 1, 24, 2),
    ]
    assert ';' in body['issues'][0]['message']
    assert body['words'] == 7
    assert body['seconds'] == 2.7


def test_ac1_lint_endpoint_needs_the_token(api):
    assert api.client.post('/narration/lint', json={'text': 'Hola.'}).status_code == 401

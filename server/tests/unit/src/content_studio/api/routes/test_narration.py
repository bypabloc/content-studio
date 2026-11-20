"""POST /narration/lint (spec 006, AC-1): incidencias con línea, columna, largo y texto, y la duración."""

from __future__ import annotations

from content_studio import messages


def test_ac2_the_lint_messages_follow_the_accepted_language(api):
    headers = {**api.headers, 'Accept-Language': 'pt'}

    issues = api.client.post('/narration/lint', json={'text': 'Hola mundo'}, headers=headers).json()['issues']

    assert issues
    first = issues[0]
    assert first['message'] == messages.t(f'lint.rule_{first["rule"]}', 'pt', **first['params'])


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


def test_a_script_longer_than_the_limit_is_422(api):
    """El linter no acepta textos sin tope: sus expresiones tardan más cuanto más largo es el texto."""
    response = api.client.post('/narration/lint', json={'text': 'a' * 20_001}, headers=api.headers)

    assert response.status_code == 422

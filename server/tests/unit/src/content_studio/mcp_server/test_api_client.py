"""Spec 029, fase 1: el cliente HTTP del puente: token e idioma en cada llamada, y los errores de la API."""

import io
import json
import urllib.error

import pytest

from content_studio.mcp_server.api_client import Api, ApiFailure


def test_post_sends_token_language_and_json(monkeypatch):
    seen: dict = {}

    def fake_urlopen(request, timeout):
        seen['url'] = request.full_url
        seen['method'] = request.get_method()
        seen['headers'] = {key.lower(): value for key, value in request.header_items()}
        seen['body'] = request.data
        seen['timeout'] = timeout
        return io.BytesIO(b'{"id": 3}')

    monkeypatch.setattr('urllib.request.urlopen', fake_urlopen)
    api = Api('http://127.0.0.1:41830/', 'token-de-prueba', language='en', timeout=5)
    assert api.post('/jobs', {'kind': 'music'}) == {'id': 3}
    assert seen['url'] == 'http://127.0.0.1:41830/jobs'
    assert seen['method'] == 'POST'
    assert seen['headers']['authorization'] == 'Bearer token-de-prueba'
    assert seen['headers']['accept-language'] == 'en'
    assert json.loads(seen['body']) == {'kind': 'music'}
    assert seen['timeout'] == 5


def test_http_error_arrives_as_api_failure_with_body(monkeypatch):
    def fake_urlopen(request, timeout):
        body = io.BytesIO(b'{"errors": [{"code": "unknown_engine"}]}')
        raise urllib.error.HTTPError(request.full_url, 422, 'Unprocessable', {}, body)

    monkeypatch.setattr('urllib.request.urlopen', fake_urlopen)
    with pytest.raises(ApiFailure) as error:
        Api('http://127.0.0.1:41830', 'token-de-prueba').post('/jobs', {})
    assert error.value.status == 422
    assert error.value.body == {'errors': [{'code': 'unknown_engine'}]}


@pytest.mark.parametrize('raw', [b'', b'no es json'])
def test_non_json_response_returns_none(monkeypatch, raw):
    monkeypatch.setattr('urllib.request.urlopen', lambda request, timeout: io.BytesIO(raw))
    assert Api('http://127.0.0.1:41830', 'token-de-prueba').get('/jobs') is None

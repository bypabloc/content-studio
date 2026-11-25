"""Integraciones (spec 029, AC-10): la configuración MCP de cada cliente se pide a la API con el token."""

import pytest

from content_studio.mcp_server.config import CLIENTS


@pytest.mark.parametrize('client', CLIENTS)
def test_mcp_config_returns_the_fragment_of_each_client(api, client):
    response = api.client.get('/integrations/mcp-config', params={'client': client}, headers=api.headers)
    assert response.status_code == 200
    body = response.json()
    assert body['client'] == client
    assert 'content-studio' in body['fragment']
    assert api.token not in body['fragment']


def test_mcp_config_rejects_an_unknown_client(api):
    response = api.client.get('/integrations/mcp-config', params={'client': 'notepad'}, headers=api.headers)
    assert response.status_code == 422

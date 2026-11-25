"""Token de Hugging Face: se guarda, `configured` lo confirma y la API genérica no lo expone (spec 034, AC-4)."""

TOKEN = 'hf_' + 'a' * 34


def test_ac4_never_returns_the_token(api):
    """AC-4: el token se guarda y configured lo confirma; ninguna respuesta lo devuelve."""
    assert api.client.get('/credentials/huggingface', headers=api.headers).json() == {'configured': False}

    saved = api.client.put('/credentials/huggingface', json={'token': TOKEN}, headers=api.headers)
    assert saved.status_code == 200
    assert saved.json() == {'configured': True}
    assert TOKEN not in saved.text

    read = api.client.get('/credentials/huggingface', headers=api.headers)
    assert read.json() == {'configured': True}
    assert TOKEN not in read.text


def test_ac4_the_generic_settings_api_refuses_the_secret(api):
    """AC-4: GET y PUT de /settings/secret.* responden 403 y no devuelven el valor."""
    api.client.put('/credentials/huggingface', json={'token': TOKEN}, headers=api.headers)

    read = api.client.get('/settings/secret.huggingface.token', headers=api.headers)
    written = api.client.put('/settings/secret.huggingface.token', json={'value': TOKEN}, headers=api.headers)

    assert read.status_code == 403
    assert written.status_code == 403
    assert read.json()['code'] == 'secret_setting'
    assert TOKEN not in read.text + written.text


def test_ac4_rejects_a_malformed_token_and_deletes_the_saved_one(api):
    """AC-4: un token sin el formato hf_ responde 422; DELETE deja configured en false."""
    rejected = api.client.put('/credentials/huggingface', json={'token': 'abc'}, headers=api.headers)
    assert rejected.status_code == 422
    assert rejected.json()['code'] == 'invalid_token'

    api.client.put('/credentials/huggingface', json={'token': TOKEN}, headers=api.headers)
    deleted = api.client.delete('/credentials/huggingface', headers=api.headers)
    assert deleted.json() == {'configured': False}

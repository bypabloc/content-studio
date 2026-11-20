"""Token de la API (spec 004, D-5, AC-6) y errores en el idioma de Accept-Language (spec 007, AC-2 y D-4).

El AC-2 usa `/jobs/nope`, pero `job_id` es entero en la ruta: FastAPI rechaza `nope` con 422 antes de llegar al error de
dominio (ficha WARNING 007-job-id-entero). Por eso estas pruebas usan un id numérico que no existe.
"""

from __future__ import annotations

from content_studio import messages, paths
from content_studio.api.app import create_app


def test_ac2_job_not_found_answers_in_the_accepted_language(api):
    headers = {**api.headers, 'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'}

    body = api.client.get('/jobs/999', headers=headers).json()

    assert body == {
        'code': 'job_not_found',
        'params': {'job_id': 999},
        'message': messages.t('error.job_not_found', 'pt', job_id=999),
    }
    assert body['message'] != messages.t('error.job_not_found', 'es', job_id=999)


def test_ac2_english_is_answered_in_english(api):
    body = api.client.get('/jobs/999', headers={**api.headers, 'Accept-Language': 'en'}).json()

    assert body['message'] == messages.t('error.job_not_found', 'en', job_id=999)


def test_ac2_an_unsupported_language_is_answered_in_spanish(api):
    body = api.client.get('/jobs/999', headers={**api.headers, 'Accept-Language': 'fr-FR'}).json()

    assert body['message'] == messages.t('error.job_not_found', 'es', job_id=999)


def test_ac2_without_the_header_the_answer_is_in_spanish(api):
    body = api.client.get('/jobs/999', headers=api.headers).json()

    assert body['message'] == messages.t('error.job_not_found', 'es', job_id=999)


def test_ac2_an_unknown_route_answers_with_its_http_code_and_text(api):
    response = api.client.get('/ruta/que/no/existe', headers={'Accept-Language': 'en'})

    assert response.status_code == 404
    assert response.json() == {'code': 'http.404', 'params': {}, 'message': messages.t('error.http.404', 'en')}


def test_ac6_every_endpoint_needs_the_bearer_token(api):
    assert api.client.get('/health').status_code == 401
    assert api.client.get('/health', headers={'Authorization': 'Bearer otro'}).status_code == 401
    assert api.client.get('/health', headers=api.headers).status_code == 200


def test_query_token_is_not_accepted_outside_files_and_events(api):
    assert api.client.get('/health', params={'token': api.token}).status_code == 401


def test_the_401_body_has_a_code_and_a_message(api):
    body = api.client.get('/health').json()

    assert body['code'] == 'unauthorized'
    assert body['message']


def test_the_tauri_window_origin_can_call_the_api(api):
    """La ventana de Tauri (http://tauri.localhost en Windows) llama a 127.0.0.1: el preflight de CORS la deja pasar."""
    response = api.client.options(
        '/health',
        headers={
            'Origin': 'http://tauri.localhost',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'authorization',
        },
    )

    assert response.headers['access-control-allow-origin'] == 'http://tauri.localhost'


def test_another_origin_gets_no_cors_permission(api):
    response = api.client.options(
        '/health',
        headers={'Origin': 'http://evil.example', 'Access-Control-Request-Method': 'GET'},
    )

    assert 'access-control-allow-origin' not in response.headers


def test_the_files_route_serves_out_the_references_and_the_voice_catalog(tmp_path):
    """/files sirve out/, las referencias y el catálogo de voces: las muestras se reproducen desde la UI (D-5)."""
    app = create_app(tmp_path / 'base.db', 'token')

    assert {paths.OUT.resolve(), paths.REFERENCE.resolve(), paths.VOICES.resolve()} <= set(app.state.roots)

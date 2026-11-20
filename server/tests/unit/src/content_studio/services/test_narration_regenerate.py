"""Servicio narration.regenerate (spec 006, D-2): resuelve la toma de origen, valida y arma el comando del motor."""

from __future__ import annotations

import json
from contextlib import closing

import pytest

from content_studio import paths
from content_studio.db import connection, jobs, schema
from content_studio.narration.parser import ENGINES
from content_studio.services import narration_regenerate as regenerate

MODEL = 'qwen-0.6b'


@pytest.fixture
def out(tmp_path, monkeypatch):
    """Carpeta de salida y motor instalado, para que la validación llegue a la toma."""
    monkeypatch.setattr(paths, 'OUT', tmp_path / 'out')
    monkeypatch.setattr(paths, 'NARRATION', tmp_path / 'narration')
    (tmp_path / 'narration' / ENGINES[MODEL].venv).mkdir(parents=True)
    return tmp_path / 'out'


@pytest.fixture
def db(tmp_path):
    with closing(connection.connect(tmp_path / 'base.db')) as conn:
        schema.migrate(conn)
        yield conn


def take(out, blocks=3):
    """Toma de origen con su script.json; para validar no hacen falta los audios de sus bloques."""
    folder = out / 'narration' / 'take'
    folder.mkdir(parents=True)
    script = {
        'wav': 'fake-expert.wav', 'ref': 'ref.wav', 'style': 'expert', 'language': 'es', 'master': 'no',
        'lufs': -16.0, 'seed': 7, 'seeds': [7], 'segments': [{'text': f'Párrafo {i}.'} for i in range(blocks)],
        'blocks': [{'ref': 'ref.wav', 'seed': 7}] * blocks,
    }  # fmt: skip
    (folder / 'script.json').write_text(json.dumps(script), encoding='utf-8')
    return folder


def finished(conn, folder, params, group_key='narration:abc123def456') -> int:
    """Un trabajo de narración ya terminado en `folder`, como lo deja el worker."""
    job_id = jobs.insert(conn, 'narration', 'gpu', params, group_key=group_key)
    jobs.update(conn, job_id, status='done', output_dir=str(folder))
    return job_id


def codes(params) -> list[str]:
    return [error['code'] for error in regenerate.validate(params)]


def test_prepare_takes_folder_model_and_group_from_the_source_job(out, db):
    folder = take(out)
    source = finished(db, folder, {'model': MODEL, 'style': 'expert', 'text': 'Hola.'})

    params, group = regenerate.prepare(db, {'source_job': source, 'index': 1})

    assert (params['source'], params['model'], group) == (str(folder), MODEL, 'narration:abc123def456')


def test_prepare_keeps_the_voice_and_style_of_the_source_for_the_card(out, db):
    folder = take(out)
    source = finished(db, folder, {'model': MODEL, 'style': 'expert', 'voice': 'karen-savage', 'text': 'Hola.'})

    params, _ = regenerate.prepare(db, {'source_job': source, 'index': 1})

    assert (params['voice'], params['style']) == ('karen-savage', 'expert')


def test_a_source_job_that_is_not_done_is_rejected(out, db):
    queued = jobs.insert(db, 'narration', 'gpu', {'model': MODEL, 'style': 'expert', 'text': 'Hola.'})

    params, _ = regenerate.prepare(db, {'source_job': queued, 'index': 1})

    assert 'source_not_done' in codes(params)


def test_a_missing_source_job_is_rejected(out, db):
    params, _ = regenerate.prepare(db, {'source_job': 999, 'index': 1})

    assert 'source_not_done' in codes(params)


def test_a_missing_source_job_reports_only_that(out, db):
    """Sin toma no hay motor que comprobar: el único error es el de la toma (la CLI lo muestra tal cual)."""
    params, _ = regenerate.prepare(db, {'source_job': 999, 'index': 1})

    assert codes(params) == ['source_not_done']


def test_an_index_inside_the_take_is_valid(out):
    assert regenerate.validate({'model': MODEL, 'source': str(take(out)), 'index': 2}) == []


@pytest.mark.parametrize('index', [3, -1])
def test_an_index_outside_the_take_is_rejected(out, index):
    assert codes({'model': MODEL, 'source': str(take(out)), 'index': index}) == ['index_out_of_range']


def test_a_source_outside_the_output_folder_is_rejected(out, tmp_path):
    outside = tmp_path / 'elsewhere'
    outside.mkdir()
    (outside / 'script.json').write_text('{"segments": [], "blocks": []}', encoding='utf-8')

    assert codes({'model': MODEL, 'source': str(outside), 'index': 0}) == ['source_outside_out']


def test_build_command_runs_the_tts_module_from_the_take(tmp_path):
    cmd = regenerate.build_command({'model': MODEL, 'source': '/tomas/a', 'index': 1, 'seed': 5}, tmp_path / 'job')

    assert cmd[cmd.index('-m') + 1] == 'content_studio.narration.tts'
    assert cmd[cmd.index('--from-script') + 1] == '/tomas/a'
    assert cmd[cmd.index('--only') + 1] == '1'
    assert cmd[cmd.index('--seed') + 1] == '5'
    assert cmd[cmd.index('--output') + 1] == str(tmp_path / 'job')


def test_a_client_source_or_model_is_never_trusted(out, db):
    """Sin toma de origen resuelta, la carpeta y el motor que manda el cliente no cuentan: es `source_not_done`."""
    forged = take(out)  # una carpeta bajo out con script.json: lo que antes pasaba la validación

    params, _ = regenerate.prepare(db, {'source_job': 999, 'index': 1, 'source': str(forged), 'model': MODEL})

    assert codes(params) == ['source_not_done']


def test_a_boolean_index_is_not_an_index(out):
    assert codes({'model': MODEL, 'source': str(take(out)), 'index': True}) == ['index_out_of_range']


def test_a_boolean_source_job_is_not_a_job_id(out, db):
    finished(db, take(out), {'model': MODEL, 'style': 'expert', 'text': 'Hola.'})

    params, group = regenerate.prepare(db, {'source_job': True, 'index': 1})

    assert (codes(params), group) == (['source_not_done'], None)


def test_a_model_that_is_not_text_is_an_unknown_engine(out):
    assert codes({'model': ['voxcpm2'], 'source': str(take(out)), 'index': 0}) == ['unknown_engine']

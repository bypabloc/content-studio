"""Servicio `mix.render` (spec 016, D-2): agrega la ruta del `mix.json`, valida el proyecto y arma el comando."""

from __future__ import annotations

import sys
from contextlib import closing

from content_studio.db import connection, mix_projects, schema
from content_studio.services import mix_render


def _db(tmp_path):
    conn = connection.connect(tmp_path / 'base.db')
    schema.migrate(conn)
    return conn


def test_the_service_runs_on_the_cpu_not_the_gpu_lock():
    """Es ffmpeg: no carga modelos, así que no toma el candado de la GPU."""
    assert mix_render.RESOURCE == 'cpu'


def test_prepare_adds_the_document_path_of_the_project(tmp_path):
    """Con un proyecto existente, los parámetros llevan la ruta de su `mix.json`."""
    with closing(_db(tmp_path)) as conn:
        project_id = mix_projects.insert(conn, 'charla', '')
        mix_projects.set_doc_path(conn, project_id, 'out/mix/x/mix.json')

        params, _ = mix_render.prepare(conn, {'mix_id': project_id})

    assert params == {'mix_id': project_id, 'doc': 'out/mix/x/mix.json'}


def test_prepare_leaves_the_params_alone_when_the_project_does_not_exist(tmp_path):
    """Sin proyecto no agrega nada: `validate` lo rechaza después."""
    with closing(_db(tmp_path)) as conn:
        params, _ = mix_render.prepare(conn, {'mix_id': 404})

    assert params == {'mix_id': 404}


def test_prepare_ignores_an_id_that_is_not_an_integer(tmp_path):
    """Un `mix_id` de texto no se busca en la base."""
    with closing(_db(tmp_path)) as conn:
        params, _ = mix_render.prepare(conn, {'mix_id': '3'})

    assert params == {'mix_id': '3'}


def test_validate_rejects_a_project_without_document():
    """Sin `doc` el proyecto no existe: el error lleva su id."""
    assert mix_render.validate({'mix_id': 7}) == [{'code': 'mix_project_not_found', 'params': {'project_id': 7}}]


def test_validate_accepts_a_project_with_a_document():
    """Con `doc` no hay errores."""
    assert mix_render.validate({'doc': 'out/mix/x/mix.json'}) == []


def test_build_command_runs_the_render_main_with_the_document_and_the_folder(tmp_path):
    """El comando es `render_main` con el `mix.json` del proyecto y la carpeta del trabajo."""
    command = mix_render.build_command({'doc': 'out/mix/x/mix.json'}, tmp_path)

    assert command == [
        sys.executable,
        '-m',
        'content_studio.mix.render_main',
        '--project',
        'out/mix/x/mix.json',
        '--out-dir',
        str(tmp_path),
    ]

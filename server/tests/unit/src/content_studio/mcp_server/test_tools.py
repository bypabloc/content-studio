"""Spec 029, fase 1: la entrada de archivos (AC-4) y las herramientas sin SDK."""

import pytest

from content_studio.mcp_server import tools


def test_ac4_missing_input_path_gives_input_not_found(tmp_path):
    missing = tmp_path / 'no-existe.wav'
    with pytest.raises(tools.ToolError) as error:
        tools.build_job('studio_transcribe', {'input_path': str(missing)})
    assert error.value.code == 'input_not_found'
    assert error.value.params == {'path': str(missing)}


def test_ac4_existing_path_outside_out_is_queued(tmp_path):
    source = tmp_path / 'toma.wav'
    source.write_bytes(b'RIFF')
    kind, params = tools.build_job('studio_convert_media', {'input_path': str(source), 'target': 'mp3'})
    assert kind == 'media.convert'
    assert params['input'] == str(source.resolve())


def test_input_folder_is_not_followed(tmp_path):
    with pytest.raises(tools.ToolError) as error:
        tools.resolve_input(str(tmp_path))
    assert error.value.code == 'input_not_found'


def test_narrate_builds_cli_params():
    kind, params = tools.build_job('studio_narrate', {'text': 'Hola'})
    assert kind == 'narration'
    assert params == {'model': 'voxcpm2', 'style': 'expert', 'text': 'Hola'}


def test_narrate_takes_one_text_or_one_script(tmp_path):
    script = tmp_path / 'guion.txt'
    script.write_text('Hola', encoding='utf-8')
    with pytest.raises(tools.ToolError) as both:
        tools.build_job('studio_narrate', {'text': 'Hola', 'script_path': str(script)})
    assert both.value.code == 'narration_source'
    _, params = tools.build_job('studio_narrate', {'script_path': str(script)})
    assert params['file'] == [str(script.resolve())]


def test_music_requires_a_style():
    with pytest.raises(tools.ToolError) as error:
        tools.build_job('studio_make_music', {})
    assert error.value.code == 'missing_style'
    kind, params = tools.build_job('studio_make_music', {'style': ['lofi-chill'], 'duration_s': 30})
    assert (kind, params['style'], params['duration']) == ('music', ['lofi-chill'], 30)


def test_job_view_marks_waiting_gpu_with_its_holder():
    job = {'id': 7, 'kind': 'music', 'status': 'queued', 'progress': 0, 'resource': 'gpu'}
    view = tools.job_view(job, [], waiting_on='pid 42: otro')
    assert view['status'] == 'waiting_gpu'
    assert view['waiting_on'] == 'pid 42: otro'


def test_resource_link_is_a_file_uri(tmp_path):
    wav = tmp_path / 'narracion.wav'
    wav.write_bytes(b'RIFF')
    link = tools.resource_link(str(wav))
    assert link['uri'] == wav.resolve().as_uri()
    assert link['name'] == 'narracion.wav'


def test_submit_job_refuses_administrative_kinds():
    with pytest.raises(tools.ToolError) as error:
        tools.build_job('studio_submit_job', {'kind': 'engine.uninstall', 'params': {}})
    assert error.value.code == 'kind_not_allowed'
    assert error.value.params == {'kind': 'engine.uninstall'}


def test_submit_job_accepts_content_kinds():
    assert tools.build_job('studio_submit_job', {'kind': 'music', 'params': {'style': ['lofi']}}) == (
        'music',
        {'style': ['lofi']},
    )


def test_mcp_kinds_exclude_administration():
    admin = ('engine.', 'storage.', 'system.', 'voice.', 'library.', 'llm.')
    assert [kind for kind in tools.MCP_KINDS if kind.startswith(admin)] == []

"""Spec 030, fase 1: qué parámetro recibe el archivo que se suelta, por tipo (02 §4.1)."""

from pathlib import Path

from content_studio.inbox import inputs


def test_input_value_is_a_path_for_media_kinds():
    assert inputs.INPUT_PARAM['media.convert'] == 'input'
    assert inputs.input_value('media.convert', Path('a.wav')) == 'a.wav'


def test_input_value_wraps_narration_in_a_list():
    assert inputs.INPUT_PARAM['narration'] == 'file'
    assert inputs.input_value('narration', Path('guion.txt')) == ['guion.txt']

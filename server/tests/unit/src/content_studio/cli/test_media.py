"""CLI de medios (spec 015, D-6): los flags pasan a los parámetros de su servicio, un trabajo por archivo, y un uso
inválido sale con 2 antes de encolar nada."""

from __future__ import annotations

import pytest

from content_studio.cli import media as media_cli
from content_studio.cli import submit
from content_studio.cli.main import main


@pytest.fixture
def sent(monkeypatch, tmp_path):
    """Captura cada trabajo que `studio` encolaría, sin correr ffmpeg."""
    calls: list[tuple[str, dict]] = []

    def fake_run(kind, params, db, checkout):
        calls.append((kind, params))
        return 0

    monkeypatch.setattr(submit, 'run', fake_run)
    monkeypatch.setattr(media_cli, 'main_checkout', lambda start: tmp_path)
    return calls


@pytest.fixture
def media(tmp_path):
    for name in ('a.wav', 'b.wav', 'clip.mp4', 'notas.txt'):
        (tmp_path / name).write_bytes(b'')
    return tmp_path


def test_convert_sends_one_job_per_file_with_its_options(sent, media):
    assert main(['convert', str(media / 'a.wav'), str(media / 'b.wav'), '--target', 'mp3', '--option', 'vbr=2']) == 0

    assert [kind for kind, _ in sent] == ['media.convert', 'media.convert']
    assert sent[0][1] == {'input': str(media / 'a.wav'), 'target': 'mp3', 'options': {'vbr': 2}}


def test_convert_social_frame_goes_into_the_options(sent, media):
    main(
        [
            'convert',
            str(media / 'clip.mp4'),
            '--target',
            'mp4-h264',
            '--option',
            'width=1080',
            '--option',
            'height=1920',
            '--reframe',
            'center',
        ]
    )

    assert sent[0][1]['options'] == {'width': 1080, 'height': 1920, 'reframe': {'mode': 'center'}}


def test_convert_option_without_an_equal_sign_is_a_usage_error(sent, media):
    with pytest.raises(SystemExit) as exit_info:
        main(['convert', str(media / 'a.wav'), '--target', 'mp3', '--option', 'vbr2'])

    assert exit_info.value.code == 2
    assert sent == []


def test_normalize_defaults_to_the_podcast_preset(sent, media):
    assert main(['normalize', str(media / 'a.wav')]) == 0

    assert sent == [('media.normalize', {'input': str(media / 'a.wav'), 'preset': 'podcast', 'enhance': False})]


def test_normalize_custom_takes_the_target_in_lufs(sent, media):
    main(['normalize', str(media / 'a.wav'), '--preset', 'custom', '--target', '-14', '--enhance'])

    assert sent[0][1] == {'input': str(media / 'a.wav'), 'preset': 'custom', 'enhance': True, 'target': -14.0}


def test_normalize_custom_without_a_target_is_a_usage_error(sent, media):
    with pytest.raises(SystemExit) as exit_info:
        main(['normalize', str(media / 'a.wav'), '--preset', 'custom'])

    assert exit_info.value.code == 2
    assert sent == []


def test_trim_keeps_the_stretch_with_its_fade_in(sent, media):
    main(['trim', str(media / 'a.wav'), '--start', '1.5', '--end', '4', '--fade-in', '0.5'])

    assert sent == [
        (
            'media.trim',
            {'input': str(media / 'a.wav'), 'start': 1.5, 'end': 4.0, 'mode': 'keep', 'fade_in': 0.5, 'fade_out': 0.0},
        )
    ]


def test_concat_joins_the_files_in_order_with_a_crossfade(sent, media):
    main(['concat', str(media / 'a.wav'), str(media / 'b.wav'), '--crossfade', '0.5'])

    assert sent == [('media.concat', {'inputs': [str(media / 'a.wav'), str(media / 'b.wav')], 'crossfade': 0.5})]


def test_split_takes_markers_or_every_but_not_both(sent, media):
    main(['split', str(media / 'a.wav'), '--markers', '2', '5.5'])
    main(['split', str(media / 'a.wav'), '--every', '10'])

    assert sent == [
        ('media.split', {'input': str(media / 'a.wav'), 'copy': False, 'markers': [2.0, 5.5]}),
        ('media.split', {'input': str(media / 'a.wav'), 'copy': False, 'every': 10.0}),
    ]
    with pytest.raises(SystemExit) as exit_info:
        main(['split', str(media / 'a.wav'), '--markers', '2', '--every', '3'])
    assert exit_info.value.code == 2


def test_a_missing_file_exits_2_before_queuing_anything(sent, media):
    assert main(['convert', str(media / 'nope.wav'), '--target', 'mp3']) == 2

    assert sent == []


def test_a_file_that_is_not_media_exits_2_before_queuing_anything(sent, media):
    assert main(['normalize', str(media / 'notas.txt')]) == 2

    assert sent == []


def test_convert_help_lists_its_flags(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(['convert', '--help'])

    assert exit_info.value.code == 0
    out = capsys.readouterr().out
    assert '--target' in out and '--option' in out and '--reframe' in out

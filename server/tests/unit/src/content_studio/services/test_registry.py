"""Registro de servicios (spec 004, D-2): cada tipo de trabajo expone `validate` y `build_command`."""

from __future__ import annotations

from content_studio.services import (
    clean_analyze,
    clean_render,
    editor_proxy,
    editor_render,
    engine_install,
    engine_uninstall,
    engine_verify,
    library_scan,
    media_concat,
    media_convert,
    media_normalize,
    media_reframe_track,
    media_split,
    media_trim,
    mix_render,
    music,
    music_samples,
    narration,
    narration_regenerate,
    storage_move,
    subtitles_burn,
    subtitles_create,
    subtitles_translate,
    system_install_tool,
    transcribe,
    voice_build,
    voice_check,
)
from content_studio.services.registry import SERVICES


def test_every_kind_exposes_validate_and_build_command():
    expected = {
        'narration': narration,
        'transcribe': transcribe,
        'clean.analyze': clean_analyze,
        'clean.render': clean_render,
        'music': music,
        'music.samples': music_samples,
        'narration.regenerate': narration_regenerate,
        'voice.check': voice_check,
        'voice.build': voice_build,
        'subtitles.create': subtitles_create,
        'subtitles.burn': subtitles_burn,
        'subtitles.translate': subtitles_translate,
        'storage.move': storage_move,
        'system.install_tool': system_install_tool,
        'engine.install': engine_install,
        'engine.uninstall': engine_uninstall,
        'engine.verify': engine_verify,
        'media.reframe_track': media_reframe_track,
        'media.normalize': media_normalize,
        'media.convert': media_convert,
        'media.trim': media_trim,
        'media.concat': media_concat,
        'media.split': media_split,
        'mix.render': mix_render,
        'editor.render': editor_render,
        'editor.proxy': editor_proxy,
        'library.scan': library_scan,
    }
    assert expected == SERVICES
    for service in SERVICES.values():
        assert callable(service.validate)
        assert callable(service.build_command)

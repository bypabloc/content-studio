"""Registro de servicios (spec 004, D-2): cada tipo de trabajo expone `validate` y `build_command`."""

from __future__ import annotations

from content_studio.services import (
    clean_analyze,
    clean_render,
    engine_install,
    engine_uninstall,
    engine_verify,
    media_reframe_track,
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
    }
    assert expected == SERVICES
    for service in SERVICES.values():
        assert callable(service.validate)
        assert callable(service.build_command)

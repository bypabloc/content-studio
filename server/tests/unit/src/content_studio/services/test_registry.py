"""Registro de servicios (spec 004, D-2): cada tipo de trabajo expone `validate` y `build_command`."""

from __future__ import annotations

from content_studio.services import music, music_samples, narration, narration_regenerate, voice_build, voice_check
from content_studio.services.registry import SERVICES


def test_every_kind_exposes_validate_and_build_command():
    expected = {
        'narration': narration,
        'music': music,
        'music.samples': music_samples,
        'narration.regenerate': narration_regenerate,
        'voice.check': voice_check,
        'voice.build': voice_build,
    }
    assert expected == SERVICES
    for service in SERVICES.values():
        assert callable(service.validate)
        assert callable(service.build_command)

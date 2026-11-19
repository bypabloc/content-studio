"""Registro de servicios (spec 004, D-2): cada tipo de trabajo expone `validate` y `build_command`."""

from __future__ import annotations

from content_studio.services import music, narration, narration_regenerate
from content_studio.services.registry import SERVICES


def test_every_kind_exposes_validate_and_build_command():
    assert {'narration': narration, 'music': music, 'narration.regenerate': narration_regenerate} == SERVICES
    for service in SERVICES.values():
        assert callable(service.validate)
        assert callable(service.build_command)

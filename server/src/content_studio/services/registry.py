"""Servicios por tipo de trabajo: la API, el worker y el CLI usan los mismos (spec 004, D-2)."""

from content_studio.services import (
    engine_install,
    engine_uninstall,
    engine_verify,
    music,
    music_samples,
    narration,
    narration_regenerate,
    storage_move,
    system_install_tool,
    transcribe,
    voice_build,
    voice_check,
)

SERVICES = {
    'narration': narration,
    'transcribe': transcribe,
    'music': music,
    'music.samples': music_samples,
    'narration.regenerate': narration_regenerate,
    'voice.check': voice_check,
    'voice.build': voice_build,
    storage_move.KIND: storage_move,
    system_install_tool.KIND: system_install_tool,
    engine_install.KIND: engine_install,
    engine_uninstall.KIND: engine_uninstall,
    engine_verify.KIND: engine_verify,
}

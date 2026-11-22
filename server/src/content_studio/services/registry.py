"""Servicios por tipo de trabajo: la API, el worker y el CLI usan los mismos (spec 004, D-2)."""

from content_studio.services import (
    clean_analyze,
    clean_render,
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
    'clean.analyze': clean_analyze,
    'clean.render': clean_render,
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

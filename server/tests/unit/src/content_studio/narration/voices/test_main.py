"""La entrada del catálogo de voces (spec 010, AC-7): la usan el CLI y la cola de trabajos."""

from __future__ import annotations

import sys

from content_studio.common import process
from content_studio.narration.voices import main as voices_main


def test_bug_voices_cli_switches_the_console_to_replace_before_printing(monkeypatch):
    """Un resultado con ← (un estilo rechazado con comprobaciones) reventaba en la consola de Windows (cp1252) antes de
    guardar la voz. La entrada pone la consola en errors='replace', igual que studio y la música."""
    calls = []
    monkeypatch.setattr(process, 'console_utf8', lambda: calls.append(True))
    monkeypatch.setattr(sys, 'argv', ['voices'])

    voices_main.main()  # sin --build solo lista el catálogo: no carga ningún modelo

    assert calls == [True]

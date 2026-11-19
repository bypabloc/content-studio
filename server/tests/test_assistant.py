"""El menú y el asistente con teclas reales: prompt_toolkit lee de una tubería y lanzar() solo captura el argv."""

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from content_studio.cli import flow, menu
from content_studio.cli.commands import por_key

ENTER, BELOW = '\r', '\x1b[B'


class Launched(Exception):
    pass


@pytest.fixture
def drive(monkeypatch):
    def capture(cmd, args):
        raise Launched(cmd.key, args)

    monkeypatch.setattr(flow, 'lanzar', capture)
    monkeypatch.setattr(menu, 'lanzar', capture)

    def drive(keys, f, *a):
        with create_pipe_input() as entry, create_app_session(input=entry, output=DummyOutput()):
            entry.send_text(keys)
            with pytest.raises(Launched) as e:
                f(*a)
        return e.value.args

    return drive


def test_assistant_asks_for_the_source_and_keeps_zero(drive):
    # Grupo excluyente → --text (1.º) → "hola" → Ejecutar
    key, argv = drive(ENTER + 'hola' + ENTER + ENTER, flow.assistant, por_key('narration tts'), ['--seed', '0'])
    assert (key, argv) == ('narration tts', ['--text', 'hola', '--seed', '0'])


def test_menu_leads_to_the_music_assistant(drive, monkeypatch):
    # Sin los venvs (CI, clon nuevo) los dos modelos salen deshabilitados y no hay nada que elegir.
    from content_studio.music.engines.base import MusicSpec

    monkeypatch.setattr(MusicSpec, 'installed', lambda self: True)
    # music es el 4.º → --model acestep (1.º) → Ejecutar
    assert drive(BELOW * 3 + ENTER + ENTER + ENTER, menu.menu) == ('music', ['--model', 'acestep'])

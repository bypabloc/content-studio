"""El menú y el asistente con teclas reales: prompt_toolkit lee de una tubería y lanzar() solo captura el argv."""

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from content_studio.cli import flujo, menu
from content_studio.cli.comandos import por_clave

ENTER, ABAJO = '\r', '\x1b[B'


class Lanzado(Exception):
    pass


@pytest.fixture
def correr(monkeypatch):
    def capturar(cmd, args):
        raise Lanzado(cmd.clave, args)

    monkeypatch.setattr(flujo, 'lanzar', capturar)
    monkeypatch.setattr(menu, 'lanzar', capturar)

    def correr(teclas, f, *a):
        with create_pipe_input() as entrada, create_app_session(input=entrada, output=DummyOutput()):
            entrada.send_text(teclas)
            with pytest.raises(Lanzado) as e:
                f(*a)
        return e.value.args

    return correr


def test_asistente_pide_la_fuente_y_conserva_el_cero(correr):
    # Grupo excluyente → --texto (1.º) → "hola" → Ejecutar
    clave, argv = correr(
        ENTER + 'hola' + ENTER + ENTER, flujo.asistente, por_clave('narration tts'), ['--semilla', '0']
    )
    assert (clave, argv) == ('narration tts', ['--texto', 'hola', '--semilla', '0'])


def test_menu_lleva_al_asistente_de_music(correr, monkeypatch):
    # Sin los venvs (CI, clon nuevo) los dos modelos salen deshabilitados y no hay nada que elegir.
    from content_studio.music.motores.base import EspecMusica

    monkeypatch.setattr(EspecMusica, 'instalado', lambda self: True)
    # music es el 4.º → --modelo acestep (1.º) → Ejecutar
    assert correr(ABAJO * 3 + ENTER + ENTER + ENTER, menu.menu) == ('music', ['--modelo', 'acestep'])

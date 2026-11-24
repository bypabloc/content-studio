"""Servicio `transcribe` de la cola (spec 013, D-2 y D-4): valida los parámetros y arma el comando del servicio."""

from __future__ import annotations

from pathlib import Path

from content_studio.services import transcribe


def test_the_service_runs_on_the_gpu_lock():
    """La transcripción usa la GPU: la cola la corre con el candado."""
    assert transcribe.RESOURCE == 'gpu'


def test_validate_accepts_a_known_model_and_language(tmp_path):
    """Un modelo del catálogo y un idioma conocido no dan errores."""
    assert transcribe.validate({'input': str(tmp_path / 'a.mp4'), 'model': 'small', 'language': 'es'}) == []


def test_validate_names_an_unknown_model():
    """Un modelo que no está en el catálogo da `unknown_engine`."""
    errors = transcribe.validate({'input': 'a.mp4', 'model': 'nope', 'language': 'es'})

    assert errors == [{'code': 'unknown_engine', 'params': {'model': 'nope'}}]


def test_validate_names_an_unknown_language():
    """Un idioma fuera de la lista da `unknown_language`; «auto» es válido."""
    errors = transcribe.validate({'input': 'a.mp4', 'model': 'small', 'language': 'xx'})

    assert errors == [{'code': 'unknown_language', 'params': {'language': 'xx'}}]
    assert transcribe.validate({'input': 'a.mp4', 'model': 'small', 'language': 'auto'}) == []


def test_build_command_passes_input_model_language_and_the_out_file(tmp_path: Path):
    """El comando corre `transcribe_main` con los flags y el JSON de salida en la carpeta del trabajo."""
    command = transcribe.build_command({'input': 'a.mp4', 'model': 'small', 'language': 'es'}, tmp_path)

    assert command[1:3] == ['-m', 'content_studio.transcription.transcribe_main']
    options = dict(zip(command[3::2], command[4::2], strict=False))
    assert options == {
        '--input': 'a.mp4',
        '--model': 'small',
        '--language': 'es',
        '--out': str(tmp_path / 'words.json'),
    }

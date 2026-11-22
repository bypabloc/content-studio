"""Servicio `media.normalize` de la cola (spec 015, D-4): valida el preset y la ruta, y arma el comando del CLI."""

from __future__ import annotations

from pathlib import Path

from content_studio import paths
from content_studio.services import media_normalize


def test_the_service_runs_on_cpu_without_the_gpu_lock():
    """Normalizar es ffmpeg: la cola no toma el candado de la GPU."""
    assert media_normalize.RESOURCE == 'cpu'


def test_validate_accepts_a_known_preset_and_a_file_outside_reference(tmp_path):
    """Un preset del catálogo y un archivo fuera de `reference/` no dan errores."""
    assert media_normalize.validate({'input': str(tmp_path / 'a.wav'), 'preset': 'podcast'}) == []


def test_validate_names_an_unknown_preset():
    """Un preset que no existe da `unknown_preset`."""
    errors = media_normalize.validate({'input': 'a.wav', 'preset': 'nope'})

    assert errors == [{'code': 'unknown_preset', 'params': {'preset': 'nope'}}]


def test_validate_refuses_a_voice_reference():
    """AC-6: un archivo dentro de `reference/` da `reference_protected`."""
    errors = media_normalize.validate({'input': str(paths.references_dir() / 'voz' / 'a.wav'), 'preset': 'podcast'})

    assert errors == [{'code': 'reference_protected', 'params': {}}]


def test_build_command_writes_the_file_and_the_report_in_the_job_folder(tmp_path: Path):
    """El comando corre `normalize` con el preset; el archivo conserva su extensión y el reporte es result.json."""
    command = media_normalize.build_command({'input': 'a.mp4', 'preset': 'youtube'}, tmp_path)

    assert command[1:3] == ['-m', 'content_studio.media.normalize']
    options = dict(zip(command[3::2], command[4::2], strict=False))
    assert options == {
        '--input': 'a.mp4',
        '--out': str(tmp_path / 'normalized.mp4'),
        '--preset': 'youtube',
        '--report': str(tmp_path / 'result.json'),
    }


def test_build_command_adds_the_custom_target_and_the_voice_chain_when_asked(tmp_path: Path):
    """Con el preset `custom` va el objetivo; «mejorar voz» agrega --enhance."""
    command = media_normalize.build_command(
        {'input': 'a.wav', 'preset': 'custom', 'target': -18.5, 'enhance': True}, tmp_path
    )

    assert command[command.index('--target') + 1] == '-18.5'
    assert command[-1] == '--enhance'

"""AC-5 (spec 015, D-3, T4), `-m local`: YuNet corre en `.venv-vision`, sigue una cara real y no inventa una
en un círculo.

Necesita el motor `vision` instalado (`studio engines install vision`), que baja OpenCV y el modelo.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from content_studio.common import process
from content_studio.vision import face_track_main

pytestmark = pytest.mark.local

PHOTO = Path(__file__).resolve().parents[1] / 'fixtures' / 'vision' / 'face.jpg'
ENGINE_READY = process.python_de(face_track_main._venv()).is_file() and face_track_main.model().is_file()
needs_engine = pytest.mark.skipif(not ENGINE_READY, reason='falta el motor vision: studio engines install vision')


def _python() -> str:
    return str(process.python_de(face_track_main._venv()))


def _track(video: Path, out: Path) -> dict:
    """Corre el seguimiento en `.venv-vision`, como lo hace el servicio `media.reframe_track`."""
    subprocess.run(
        [_python(), '-m', 'content_studio.vision.face_track_main', '--input', str(video), '--out', str(out)],
        check=True,
        capture_output=True,
        env=process.env_src(),
    )
    return json.loads(out.read_text(encoding='utf-8'))


def _faces(video: Path) -> list:
    """Las caras que YuNet encuentra en cada muestra del video, sin suavizar."""
    probe = (
        'import json, sys\n'
        'from pathlib import Path\n'
        'from content_studio.vision import face_track_main as f\n'
        'faces, _, _ = f.detect(Path(sys.argv[1]), f.model())\n'
        'print(json.dumps(faces))\n'
    )
    run = subprocess.run(
        [_python(), '-c', probe, str(video)], check=True, capture_output=True, text=True, env=process.env_src()
    )
    return json.loads(run.stdout)


def _disc(tmp_path: Path) -> Path:
    """Un círculo claro de 2 s sobre fondo oscuro: lo que YuNet no reconoce como cara."""
    path = tmp_path / 'disc.mp4'
    subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-hide_banner',
            '-loglevel',
            'error',
            '-f',
            'lavfi',
            '-i',
            'color=c=black:s=640x360:r=25:d=2',
            '-vf',
            "geq=lum='if(lt(hypot(X-320,Y-180),120),220,16)':cb=128:cr=128",
            '-c:v',
            'libx264',
            '-pix_fmt',
            'yuv420p',
            str(path),
        ],
        check=True,
    )
    return path


@needs_engine
def test_ac5_a_disc_without_a_face_keeps_the_track_at_the_center(tmp_path):
    """AC-5: un círculo que YuNet no toma por cara deja la trayectoria en el centro (0,5), 5 muestras por segundo."""
    track = _track(_disc(tmp_path), tmp_path / 'track.json')

    assert track['fps'] == 5.0
    assert (track['width'], track['height']) == (640, 360)
    assert len(track['centers']) == 10
    assert all(abs(center - 0.5) < 1e-9 for center in track['centers'])


@needs_engine
@pytest.mark.skipif(
    not PHOTO.is_file(), reason='falta una foto con cara y licencia clara: ver PENDING 015-foto-de-prueba'
)
def test_ac5_yunet_finds_a_real_face_in_the_test_photo(tmp_path):
    """AC-5: YuNet encuentra la cara de la foto de prueba en al menos una muestra."""
    video = tmp_path / 'face.mp4'
    subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-hide_banner',
            '-loglevel',
            'error',
            '-loop',
            '1',
            '-i',
            str(PHOTO),
            '-t',
            '2',
            '-r',
            '25',
            '-c:v',
            'libx264',
            '-pix_fmt',
            'yuv420p',
            str(video),
        ],
        check=True,
    )

    assert any(faces for faces in _faces(video))

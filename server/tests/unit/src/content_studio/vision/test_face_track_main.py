"""AC-5 (spec 015, D-3, T4): la cara que se sigue. Entre las grandes, la más cercana a la anterior; sin caras, ninguna
posición. Funciones puras: no necesitan OpenCV ni el venv de visión."""

from __future__ import annotations

import json
import sys
import types

from content_studio.vision import face_track_main as track

FRAME_W = 1920


def test_the_largest_face_is_followed_when_there_is_no_history():
    """Sin historia, la cara de mayor área: su centro en x, normalizado."""
    faces = [(100, 200, 60, 60), (1200, 300, 200, 200)]  # (x, y, w, h); la segunda es mucho más grande

    assert track.choose_face(faces, FRAME_W, previous=None) == (1200 + 100) / FRAME_W


def test_among_similar_faces_the_one_nearest_to_the_previous_position_wins():
    """Dos caras casi del mismo tamaño: la más cercana a la posición anterior (continuidad)."""
    faces = [(200, 200, 200, 200), (1400, 200, 200, 200)]  # las dos son de 200 px de lado

    assert track.choose_face(faces, FRAME_W, previous=0.15) == (200 + 100) / FRAME_W
    assert track.choose_face(faces, FRAME_W, previous=0.8) == (1400 + 100) / FRAME_W


def test_no_face_gives_no_position():
    """Sin caras, no hay posición (None): la trayectoria conserva la última."""
    assert track.choose_face([], FRAME_W, previous=0.5) is None


def test_one_sample_per_sampled_frame_and_none_where_there_is_no_face():
    """Una muestra por cuadro muestreado; sin cara, la muestra es None (la suavización conserva la última)."""
    detections = [[(0, 0, 300, 300)], [], [], [(1500, 0, 300, 300)]]

    samples = track.track_faces(detections, FRAME_W)

    assert len(samples) == 4
    assert samples[0] == 150 / FRAME_W
    assert samples[1] is None and samples[2] is None
    assert samples[3] == (1500 + 150) / FRAME_W


def _fake_cv2(monkeypatch, fps: float, frames: int, width: int, height: int, faces: list) -> None:
    """Un `cv2` falso en `sys.modules`: un video de `frames` cuadros y un detector que da `faces`, una lista por
    llamada. OpenCV solo existe en `.venv-vision`; así `detect` se prueba en el venv general."""
    detections = iter(faces)

    class Capture:
        def __init__(self, _path: str) -> None:
            self._frames = list(range(frames))

        def get(self, prop: int) -> float:
            return {3: float(width), 4: float(height), 5: fps}[prop]

        def read(self) -> tuple[bool, int | None]:
            return (True, self._frames.pop(0)) if self._frames else (False, None)

        def release(self) -> None:
            pass

    class Detector:
        def detect(self, _frame: int) -> tuple[int, list | None]:
            return 0, next(detections)

    fake = types.ModuleType('cv2')
    fake.CAP_PROP_FRAME_WIDTH, fake.CAP_PROP_FRAME_HEIGHT, fake.CAP_PROP_FPS = 3, 4, 5
    fake.VideoCapture = Capture
    fake.FaceDetectorYN = types.SimpleNamespace(create=lambda *_args: Detector())
    monkeypatch.setitem(sys.modules, 'cv2', fake)


def test_detect_samples_five_frames_per_second_and_reads_each_face_box(monkeypatch, tmp_path):
    """Un video de 10 cuadros por segundo se muestrea cada dos cuadros (5 por segundo); las cajas son (x, y, w, h)."""
    _fake_cv2(
        monkeypatch, fps=10.0, frames=6, width=640, height=360, faces=[[[10, 20, 30, 40]], [], [[50, 60, 70, 80]]]
    )

    found, width, height = track.detect(tmp_path / 'clip.mp4', tmp_path / 'model.onnx')

    assert (width, height) == (640, 360)
    assert found == [[(10.0, 20.0, 30.0, 40.0)], [], [(50.0, 60.0, 70.0, 80.0)]]


def test_detect_falls_back_to_five_frames_per_second_when_the_video_has_no_rate(monkeypatch, tmp_path):
    """Sin tasa de cuadros, `detect` toma 5 por segundo: cada cuadro es una muestra."""
    _fake_cv2(monkeypatch, fps=0.0, frames=3, width=320, height=240, faces=[[], [], []])

    found, _, _ = track.detect(tmp_path / 'clip.mp4', tmp_path / 'model.onnx')

    assert found == [[], [], []]


def test_the_track_service_flags_are_input_and_out():
    args = track.build_parser().parse_args(['--input', 'clip.mp4', '--out', 'track.json'])

    assert (args.input, args.out) == ('clip.mp4', 'track.json')


def test_main_writes_the_smoothed_centers_with_the_video_size(monkeypatch, tmp_path):
    """El servicio relanza en su venv, detecta, suaviza y escribe `track.json` con fps y tamaño."""
    monkeypatch.setattr(track.process, 'use_venv', lambda venv, readme, module: None)
    monkeypatch.setattr(track, '_venv', lambda: tmp_path)
    monkeypatch.setattr(track, 'model', lambda: tmp_path / 'model.onnx')
    monkeypatch.setattr(track, 'detect', lambda video, model: ([[(0, 0, 300, 300)], [(1500, 0, 300, 300)]], 1920, 1080))
    out = tmp_path / 'sub' / 'track.json'

    assert track.main(['--input', 'clip.mp4', '--out', str(out)]) == 0

    data = json.loads(out.read_text(encoding='utf-8'))
    assert (data['fps'], data['width'], data['height']) == (track.FACE_FPS, 1920, 1080)
    assert len(data['centers']) == 2

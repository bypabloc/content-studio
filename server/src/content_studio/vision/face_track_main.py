"""Sigue a la persona en un video (spec 015, D-3): YuNet de OpenCV a 5 cuadros por segundo,
con la trayectoria suavizada y el resultado en `track.json`.

Corre en `.venv-vision`: `cv2` se importa dentro de `detect`, así `--help` y las funciones puras no necesitan el venv.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from content_studio import paths
from content_studio.common import process
from content_studio.engines import recipes
from content_studio.vision import smooth

README = 'server/data/narration/README.md'
FACE_FPS = 5.0  # una muestra cada 0,2 s: la trayectoria que va a `sendcmd`
LARGE = 0.5  # una cara es candidata si su área llega a esta fracción de la mayor
SPEED_LIMIT = 0.25  # el recorte se mueve, como mucho, un cuarto del ancho de la fuente por segundo
MODEL_FILE = 'face_detection_yunet_2023mar.onnx'

Face = tuple[float, float, float, float]  # x, y, ancho y alto en píxeles


def _area(face: Face) -> float:
    return face[2] * face[3]


def _center(face: Face, width: int) -> float:
    x, _, w, _ = face
    return (x + w / 2) / width


def choose_face(faces: list[Face], width: int, previous: float | None) -> float | None:
    """La posición (0–1) de la cara que se sigue, o None sin caras.

    Entre las grandes (área de al menos `LARGE` de la mayor), la más cercana a la posición anterior; sin anterior,
    la mayor.
    """
    if not faces:
        return None
    biggest = max(_area(face) for face in faces)
    large = [face for face in faces if _area(face) >= LARGE * biggest]
    if previous is None:
        return _center(max(large, key=_area), width)
    return min((_center(face, width) for face in large), key=lambda center: abs(center - previous))


def track_faces(detections: list[list[Face]], width: int) -> list[float | None]:
    """Una muestra por cuadro muestreado: la posición de la cara elegida, o None donde no hay ninguna."""
    samples: list[float | None] = []
    previous: float | None = None
    for faces in detections:
        position = choose_face(faces, width, previous)
        samples.append(position)
        if position is not None:
            previous = position
    return samples


def _face(row: Sequence[float]) -> Face:
    """La caja de una fila de YuNet: las cuatro primeras columnas, como flotantes."""
    x, y, w, h = (float(value) for value in row[:4])
    return x, y, w, h


def detect(video: Path, model: Path) -> tuple[list[list[Face]], int, int]:
    """Las caras de cada muestra de 5 cuadros por segundo, y el ancho y alto del video."""
    import cv2  # solo existe en .venv-vision

    capture = cv2.VideoCapture(str(video))
    source_fps = capture.get(cv2.CAP_PROP_FPS) or FACE_FPS
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    detector = cv2.FaceDetectorYN.create(str(model), '', (width, height), 0.8, 0.3, 5000)
    found: list[list[Face]] = []
    index = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        # la muestra k cae en el cuadro round(k × fps_fuente / 5): así el tiempo de cada muestra es k / 5 s
        if index >= round(len(found) * source_fps / FACE_FPS):
            _, faces = detector.detect(frame)
            found.append([] if faces is None else [_face(row) for row in faces])
        index += 1
    capture.release()
    return found, width, height


def build_parser() -> argparse.ArgumentParser:
    """Los flags del servicio: --input, --out."""
    parser = argparse.ArgumentParser(prog='face_track_main', description='Track the person in a video with YuNet.')
    parser.add_argument('--input', required=True, help='video to follow')
    parser.add_argument('--out', required=True, help='output JSON with the smoothed centers, 0 to 1')
    return parser


def model() -> Path:
    """El archivo .onnx de la receta `vision`, en la carpeta de sus motores."""
    recipe = recipes.load('vision')
    return paths.engine_root(recipe.family, recipe.venv, recipe.engine) / 'models' / MODEL_FILE


def _venv() -> Path:
    """El venv de la receta `vision` (su carpeta la decide `paths.engine_root`)."""
    recipe = recipes.load('vision')
    return paths.engine_root(recipe.family, recipe.venv, recipe.engine) / recipe.venv


def main(argv: list[str] | None = None) -> int:
    """Entrada del servicio: relanza en `.venv-vision`, detecta, suaviza y escribe `track.json`."""
    process.use_venv(_venv(), README, module='content_studio.vision.face_track_main')
    args = build_parser().parse_args(argv)
    detections, width, height = detect(Path(args.input), model())
    centers = smooth.smooth(track_faces(detections, width), fps=FACE_FPS, speed_limit=SPEED_LIMIT)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({'fps': FACE_FPS, 'width': width, 'height': height, 'centers': centers}), encoding='utf-8'
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())

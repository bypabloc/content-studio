"""AC-5 (spec 015, D-3, T4): la cara que se sigue. Entre las grandes, la más cercana a la anterior; sin caras, ninguna
posición. Funciones puras: no necesitan OpenCV ni el venv de visión."""

from __future__ import annotations

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

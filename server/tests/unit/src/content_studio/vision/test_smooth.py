"""AC-5 (spec 015, D-3, T4): el suavizado de la trayectoria de la cara.

Ningún paso supera el límite de velocidad, la media móvil sigue a la cara y, sin cara, se conserva la última posición.
Función pura: no necesita modelo."""

from __future__ import annotations

import pytest

from content_studio.vision import smooth

FPS = 5.0
LIMIT = 0.25  # fracción del ancho por segundo


def test_no_step_exceeds_the_speed_limit_when_the_face_jumps():
    """Una cara que salta de 0,3 a 0,8 en un cuadro: el paso sale limitado al 25 % del ancho por segundo."""
    track = [0.3] * 10 + [0.8] * 30

    out = smooth.smooth(track, fps=FPS, speed_limit=LIMIT)

    max_step = LIMIT / FPS
    steps = [abs(b - a) for a, b in zip(out, out[1:], strict=False)]
    assert max(steps) <= max_step + 1e-9


def test_the_moving_average_follows_the_face_to_its_new_place():
    """Tras el salto, la trayectoria llega a la nueva posición (la media móvil de 1 s la sigue)."""
    track = [0.3] * 10 + [0.8] * 60

    out = smooth.smooth(track, fps=FPS, speed_limit=LIMIT)

    assert out[-1] == pytest.approx(0.8, abs=1e-6)


def test_without_a_face_the_last_position_is_kept():
    """Sin cara (None) se conserva la última posición vista; antes de la primera cara, el centro."""
    track = [None, None, 0.6, 0.6, None, None]

    out = smooth.smooth(track, fps=FPS, speed_limit=LIMIT)

    assert out[-1] == pytest.approx(0.6, abs=1e-6)
    assert all(0.0 <= value <= 1.0 for value in out)


def test_with_no_face_at_all_the_track_stays_at_the_center():
    """Si nunca hay cara, la trayectoria queda en el centro (0,5)."""
    out = smooth.smooth([None] * 8, fps=FPS, speed_limit=LIMIT)

    assert out == [pytest.approx(0.5)] * 8

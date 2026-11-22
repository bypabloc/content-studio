import pytest

from content_studio.mix.envelope import gain_curve, speech_regions


def value_at(curve, t):
    """El valor de la curva en `t`, interpolado entre sus puntos."""
    for (t0, v0), (t1, v1) in zip(curve, curve[1:], strict=False):
        if t0 <= t <= t1:
            return v0 if t1 == t0 else v0 + (v1 - v0) * (t - t0) / (t1 - t0)
    raise AssertionError(f'{t} fuera de la curva')


def test_ac1_speech_regions_merges_close_words_and_adds_margins():
    """AC-1: las palabras a menos de 0,6 s se unen, y cada tramo gana 0,2 s antes y 0,4 s después."""
    assert speech_regions([(1.0, 1.4), (1.6, 2.0), (4.0, 4.5)]) == [(0.8, 2.4), (3.8, 4.9)]


def test_ac1_gain_curve_ducks_before_each_region_and_recovers_after_it():
    """AC-1: con una duración de 6 s, la música baja a -12 dB en 0,5–0,8 s, sube en 2,4–2,7, baja en 3,5–3,8 y sube
    en 4,9–5,2."""
    curve = gain_curve([(0.8, 2.4), (3.8, 4.9)], duration=6, duck_db=-12, ramp=0.3, base_db=0)

    assert curve[0][0] == 0
    assert curve[-1][0] == 6
    assert value_at(curve, 0.5) == pytest.approx(0)
    assert value_at(curve, 0.65) == pytest.approx(-6)
    assert value_at(curve, 0.8) == pytest.approx(-12)
    assert value_at(curve, 2.4) == pytest.approx(-12)
    assert value_at(curve, 2.55) == pytest.approx(-6)
    assert value_at(curve, 2.7) == pytest.approx(0)
    assert value_at(curve, 3.5) == pytest.approx(0)
    assert value_at(curve, 3.8) == pytest.approx(-12)
    assert value_at(curve, 4.9) == pytest.approx(-12)
    assert value_at(curve, 5.2) == pytest.approx(0)


def test_ac2_overlapping_ramps_make_one_valley_without_rising_in_between():
    """AC-2: dos regiones a 0,4 s una de otra con rampas de 0,3 s forman un solo valle: entre ellas no sube."""
    curve = gain_curve([(1.0, 2.0), (2.4, 3.0)], duration=6, duck_db=-12, ramp=0.3)

    ducked = [value_at(curve, 1.0 + step * 0.01) for step in range(201)]  # de 1,0 a 3,0 s
    assert all(db == pytest.approx(-12) for db in ducked)
    assert value_at(curve, 0.7) == pytest.approx(0)
    assert value_at(curve, 3.3) == pytest.approx(0)

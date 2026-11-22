"""Plan de cortes del limpiador (spec 013, ciclo 1: AC-1 y AC-2)."""

from __future__ import annotations

import pytest

from content_studio.clean.plan import keep_segments, plan, remap


def _words(*pairs: tuple[float, float]) -> list[dict]:
    return [{'start': s, 'end': e, 'word': f'w{i}'} for i, (s, e) in enumerate(pairs)]


def _spans(cuts: list[dict]) -> list[tuple[float, float]]:
    return [(c['start'], c['end']) for c in cuts]


def test_ac1_plan_cuts_gaps_above_min_gap_and_the_final_silence():
    """AC-1: huecos > 0.5 s se cortan con 0.15 s de margen; el hueco de 0.3 s no; el final también."""
    words = _words((0.0, 0.4), (1.2, 1.6), (1.9, 2.3))

    cuts = plan(words, duration=3.5, min_gap=0.5, padding=0.15)

    assert _spans(cuts) == [(0.55, 1.05), (2.45, 3.35)]
    assert all(c['enabled'] is True for c in cuts)


def test_gap_equal_to_min_gap_is_not_cut():
    """Un hueco exactamente igual a min_gap no se corta: el límite es estricto."""
    words = _words((0.0, 0.4), (0.9, 1.2))  # hueco de 0.5

    cuts = plan(words, duration=1.2, min_gap=0.5, padding=0.15, edges=False)

    assert cuts == []


def test_no_words_means_no_cuts():
    """Sin palabras no hay base para cortar: no se borra todo el archivo."""
    assert plan([], duration=10.0) == []


def test_single_word_cuts_both_edges_when_edges_is_on():
    """Una sola palabra: se corta el inicio y el final, cada uno con su margen."""
    words = _words((1.0, 1.5))

    cuts = plan(words, duration=3.0, min_gap=0.5, padding=0.15, edges=True)

    assert _spans(cuts) == [(0.0, 0.85), (1.65, 2.85)]


def test_edges_false_skips_start_and_end():
    """Con edges=False solo se cortan los huecos entre palabras."""
    words = _words((1.0, 1.5))

    assert plan(words, duration=3.0, min_gap=0.5, padding=0.15, edges=False) == []


def test_padding_bigger_than_half_the_gap_discards_the_cut():
    """Si el margen se come todo el hueco, el corte no tiene largo positivo y se descarta."""
    words = _words((0.0, 0.4), (1.2, 1.6))  # hueco de 0.8

    cuts = plan(words, duration=1.6, min_gap=0.5, padding=0.45, edges=False)

    assert cuts == []


def test_cut_shorter_than_50_ms_is_discarded():
    """Un corte de menos de 50 ms no se propone."""
    words = _words((0.0, 0.4), (1.0, 1.4))  # hueco de 0.6; con margen 0.28 quedan 0.04 s

    assert plan(words, duration=1.4, min_gap=0.5, padding=0.28, edges=False) == []


def test_keep_segments_is_the_complement_of_the_enabled_cuts():
    """Los tramos a conservar son el complemento de los cortes activos dentro de la duración."""
    cuts = [{'start': 0.55, 'end': 1.05, 'enabled': True}, {'start': 2.45, 'end': 3.35, 'enabled': True}]

    assert keep_segments(cuts, 3.5) == [(0.0, 0.55), (1.05, 2.45), (3.35, 3.5)]


def test_keep_segments_ignores_disabled_cuts():
    """Un corte desactivado no se quita: el tramo queda."""
    cuts = [{'start': 0.55, 'end': 1.05, 'enabled': False}]

    assert keep_segments(cuts, 2.0) == [(0.0, 2.0)]


def test_ac2_remap_moves_word_times_to_the_clean_timeline():
    """AC-2: las palabras pasan a [0.0–0.4] [0.7–1.1] [1.4–1.8] en el limpio, y la reasignación es monótona."""
    cuts = [{'start': 0.55, 'end': 1.05, 'enabled': True}, {'start': 2.45, 'end': 3.35, 'enabled': True}]
    words = _words((0.0, 0.4), (1.2, 1.6), (1.9, 2.3))

    new = [(round(remap(w['start'], cuts), 6), round(remap(w['end'], cuts), 6)) for w in words]

    assert new == [(0.0, 0.4), (0.7, 1.1), (1.4, 1.8)]


def test_remap_pastes_a_time_inside_a_cut_to_its_edge():
    """Un tiempo dentro de un corte se pega al inicio del corte en el limpio."""
    cuts = [{'start': 0.55, 'end': 1.05, 'enabled': True}]

    assert remap(0.8, cuts) == pytest.approx(0.55)


def test_remap_ignores_disabled_cuts():
    """Un corte desactivado no reasigna nada."""
    cuts = [{'start': 0.55, 'end': 1.05, 'enabled': False}]

    assert remap(2.0, cuts) == pytest.approx(2.0)


def test_remap_is_monotone_over_a_sequence_of_times():
    """La reasignación nunca retrocede al avanzar el tiempo original."""
    cuts = [{'start': 0.55, 'end': 1.05, 'enabled': True}, {'start': 2.45, 'end': 3.35, 'enabled': True}]
    times = [i * 0.05 for i in range(80)]

    mapped = [remap(t, cuts) for t in times]

    assert all(a <= b for a, b in zip(mapped, mapped[1:], strict=False))

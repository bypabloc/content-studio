"""Cortes editables del limpiador (spec 013, ciclo 6: AC-7): replanificar sin perder los cortes que el usuario tocó."""

from __future__ import annotations

from content_studio.clean import cuts

WORDS = [{'start': 0.0, 'end': 0.4}, {'start': 1.2, 'end': 1.6}, {'start': 1.9, 'end': 2.3}]


def _spans(items: list[dict]) -> list[tuple[float, float]]:
    return [(c['start'], c['end']) for c in items]


def test_ac7_replan_recalculates_the_untouched_cuts_with_the_new_min_gap():
    """AC-7: con min_gap 0.5 salen dos cortes; con 0.8 el hueco de 0.8 s ya no se corta, y el final sí."""
    first = cuts.replan(WORDS, duration=3.5, min_gap=0.5, padding=0.15, edges=True, previous=[])
    second = cuts.replan(WORDS, duration=3.5, min_gap=0.8, padding=0.15, edges=True, previous=first)

    assert _spans(first) == [(0.55, 1.05), (2.45, 3.35)]
    assert _spans(second) == [(2.45, 3.35)]


def test_ac7_edited_cuts_are_kept_when_replanning():
    """AC-7: un corte que el usuario editó a mano se conserva al replanificar."""
    edited = [{'start': 0.9, 'end': 1.0, 'enabled': True, 'edited': True}]

    result = cuts.replan(WORDS, duration=3.5, min_gap=0.5, padding=0.15, edges=True, previous=edited)

    assert (0.9, 1.0) in _spans(result)
    assert (0.55, 1.05) not in _spans(result)  # se solapa con el editado: el calculado cede


def test_a_disabled_cut_stays_disabled_after_replanning():
    """Un corte desactivado a mano sigue desactivado al replanificar."""
    previous = [{'start': 0.55, 'end': 1.05, 'enabled': False, 'edited': True}]

    result = cuts.replan(WORDS, duration=3.5, min_gap=0.5, padding=0.15, edges=False, previous=previous)

    assert [c['enabled'] for c in result if (c['start'], c['end']) == (0.55, 1.05)] == [False]


def test_the_cuts_document_round_trips_through_the_job_folder(tmp_path):
    """El documento de cortes (cuts.json) se guarda y se lee de la carpeta del trabajo, con sus parámetros."""
    document = {
        'params': {'min_gap': 0.5, 'padding': 0.15, 'edges': True},
        'cuts': [{'start': 1.0, 'end': 2.0, 'enabled': True}],
    }

    cuts.save(tmp_path, document)

    assert cuts.load(tmp_path) == document
    assert cuts.file_for(tmp_path) == tmp_path / 'cuts.json'

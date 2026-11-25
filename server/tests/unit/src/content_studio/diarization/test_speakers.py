"""Paleta y nombres por defecto de los hablantes (spec 035, D-6 y 3. Datos)."""

from content_studio.diarization import speakers


def test_palette_and_names_by_order():
    """La paleta sigue su orden y se repite después del octavo hablante; el nombre inicial numera desde 1."""
    assert speakers.color(0) == '#2563eb'
    assert speakers.color(7) == '#65a30d'
    assert speakers.color(8) == '#2563eb'
    assert speakers.default_name(1) == 'Hablante 1'
    assert speakers.build(['SPEAKER_00', 'SPEAKER_01']) == {
        'SPEAKER_00': {'name': 'Hablante 1', 'color': '#2563eb'},
        'SPEAKER_01': {'name': 'Hablante 2', 'color': '#dc2626'},
    }

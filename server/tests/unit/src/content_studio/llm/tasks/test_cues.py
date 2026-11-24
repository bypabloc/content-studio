"""Lo común de las tareas de subtítulos, spec 021 D-4."""

from content_studio.db import connection, schema, subtitle_projects
from content_studio.llm.tasks import cues


def test_prepare_adds_the_document_of_the_project(tmp_path):
    """El proyecto se resuelve a su documento; sin proyecto no se agrega nada (y validate lo rechaza)."""
    conn = connection.connect(tmp_path / 'base.db')
    schema.migrate(conn)
    project = subtitle_projects.insert(conn, 'demo', str(tmp_path / 'demo.mp4'), str(tmp_path / 'subtitles.json'))

    params, group = cues.prepare(conn, {'project_id': project})
    assert params['doc'] == str(tmp_path / 'subtitles.json')
    assert group is None
    assert cues.prepare(conn, {'project_id': 999})[0] == {'project_id': 999}
    assert cues.validate_project({'project_id': 999})[0]['code'] == 'subtitle_project_not_found'
    conn.close()


def test_fits_uses_the_style_limits():
    """Un texto cabe si entra en max_lines renglones de max_chars; por defecto 42×2."""
    assert cues.limits({'style': {}}) == (42, 2)
    assert cues.limits({'style': {'max_chars': 20, 'max_lines': 1}}) == (20, 1)
    assert cues.fits('palabra ' * 9, (42, 2))
    assert not cues.fits('palabra ' * 12, (42, 2))


def test_batches_carry_the_previous_cues_as_context():
    """Lotes de 30 con los 5 anteriores como contexto."""
    items = list(range(70))
    batches = list(cues.batches(items, size=30, context=5))
    assert [(len(batch), context) for batch, context in batches] == [
        (30, []),
        (30, [25, 26, 27, 28, 29]),
        (10, [55, 56, 57, 58, 59]),
    ]

"""El trabajo de reubicación cambia el almacenamiento y conserva las rutas históricas."""

from contextlib import closing

from content_studio.db import connection, schema, settings
from content_studio.services import storage_move


def test_ac7_commits_the_new_folder_and_keeps_old_output_paths(tmp_path, monkeypatch):
    """Las rutas emitidas antes de dos traslados siguen apuntando al mismo archivo."""
    database = tmp_path / 'store.db'
    original = tmp_path / 'original'
    temporary = tmp_path / 'temporary'
    final = tmp_path / 'final'
    original.mkdir()
    (original / 'track.wav').write_bytes(b'RIFF')
    monkeypatch.setenv('CONTENT_STUDIO_DB', str(database))
    with closing(connection.connect(database)) as conn:
        schema.migrate(conn)
        settings.set_value(conn, 'storage.outputs', str(original))
    storage_move.run('outputs', temporary)
    storage_move.run('outputs', final)

    assert (final / 'track.wav').read_bytes() == b'RIFF'
    assert not original.exists()
    assert not temporary.exists()
    with closing(connection.connect(database)) as conn:
        assert settings.get(conn, 'storage.outputs') == str(final)
        assert settings.get(conn, 'storage.outputs_moves') == {str(original): str(final), str(temporary): str(final)}

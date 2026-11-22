"""El modelo que el usuario eligió para transcribir (spec 013, D-7): la preferencia `select.whisper.model`."""

from __future__ import annotations

from content_studio.db import schema, settings
from content_studio.db.connection import connect
from content_studio.transcription import models


def test_without_a_database_the_recommended_model_is_selected(tmp_path):
    assert models.selected(tmp_path / 'none.sqlite') == 'large-v3-turbo'


def test_the_model_chosen_in_settings_is_the_one_selected(tmp_path):
    db = tmp_path / 'content-studio.db'
    conn = connect(db)
    schema.migrate(conn)
    settings.set_value(conn, 'select.whisper.model', 'medium')
    conn.close()

    assert models.selected(db) == 'medium'

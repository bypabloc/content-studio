"""Token de Hugging Face en settings: se guarda, se lee y se borra sin tocar otras claves (spec 034, AC-4)."""

import sqlite3

import pytest

from content_studio import credentials


def _connection() -> sqlite3.Connection:
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL)')
    return conn


def test_ac4_saves_reads_and_clears_the_token_without_touching_other_keys():
    """AC-4: el token vive en la clave secret.huggingface.token y borrarlo deja las demás preferencias."""
    conn = _connection()
    conn.execute("INSERT INTO settings VALUES ('ui.theme', '\"dark\"', 'x')")
    token = 'hf_' + 'c' * 34

    assert credentials.huggingface_token(conn) is None
    credentials.set_huggingface_token(conn, token)
    assert credentials.huggingface_token(conn) == token

    credentials.clear_huggingface_token(conn)
    assert credentials.huggingface_token(conn) is None
    assert conn.execute("SELECT value FROM settings WHERE key = 'ui.theme'").fetchone() == ('"dark"',)


@pytest.mark.parametrize(
    ('token', 'valid'),
    [('hf_' + 'd' * 20, True), ('hf_' + 'd' * 19, False), ('abc', False), ('hf_ ' + 'd' * 20, False)],
)
def test_ac4_only_tokens_with_the_huggingface_shape_are_valid(token, valid):
    """AC-4: un token es válido solo con el prefijo hf_ y al menos 20 caracteres alfanuméricos."""
    assert credentials.valid_token(token) is valid

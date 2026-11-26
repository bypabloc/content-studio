"""Spec 030, fase 1: registrar una carpeta de entrada (AC-1)."""

import pytest

from content_studio.inbox import store
from content_studio.jobs import queue


def test_ac1_registers_a_valid_folder_and_rejects_the_rest(conn, folder, services):
    with pytest.raises(store.InboxError) as missing:
        store.register(conn, str(folder.parent / 'no-existe'), 'media.convert', {'target': 'mp3'}, services=services)
    assert missing.value.code == 'inbox_path_not_found'

    with pytest.raises(store.InboxError) as unknown:
        store.register(conn, str(folder), 'engine.uninstall', {}, services=services)
    assert unknown.value.code == 'unknown_kind'

    with pytest.raises(queue.InvalidJob) as invalid:
        store.register(conn, str(folder), 'media.convert', {'target': 'bad'}, services=services)
    assert invalid.value.errors[0]['code'] == 'unknown_target'

    folder_id = store.register(conn, str(folder), 'media.convert', {'target': 'mp3'}, services=services)
    saved = store.get(conn, folder_id)
    assert saved['path'] == str(folder.resolve())
    assert saved['params'] == {'target': 'mp3'}
    assert saved['keep_awake'] is True
    assert saved['paused'] is False
    assert {'processing', 'done', 'failed'} <= {child.name for child in folder.iterdir()}

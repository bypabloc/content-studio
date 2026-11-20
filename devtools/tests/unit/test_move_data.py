"""AC-4: `move-data` mueve narration/ y music/ a server/data/ y reescribe las rutas de las instalaciones editables."""

from __future__ import annotations

import json

from devtools.move_data import main


def tree(root):
    (root / 'narration/voz').mkdir(parents=True)
    (root / 'narration/voz/clara.wav').write_bytes(b'RIFF')
    (root / 'music/models/heartlib').mkdir(parents=True)
    site = root / 'music/.venv-heartmula/Lib/site-packages'
    site.mkdir(parents=True)
    (site / '__editable__.heartlib-0.1.0.pth').write_text(str(root / 'music/models/heartlib') + '\n')
    info = site / 'heartlib-0.1.0.dist-info'
    info.mkdir()
    url = (root / 'music/models/heartlib').as_uri()
    (info / 'direct_url.json').write_text(json.dumps({'url': url, 'dir_info': {'editable': True}}))


def test_plan_without_apply_not_touches_the_disco(tmp_path, capsys):
    tree(tmp_path)
    assert main(['--root', str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)['applied'] is False
    assert (tmp_path / 'narration/voz/clara.wav').is_file() and not (tmp_path / 'server').exists()


def test_apply_moves_and_rewrites_pth_and_direct_url(tmp_path):
    tree(tmp_path)
    assert main(['--apply', '--root', str(tmp_path)]) == 0
    assert not (tmp_path / 'narration').exists() and not (tmp_path / 'music').exists()
    assert (tmp_path / 'server/data/narration/reference/default/clear.wav').is_file()  # paso 2 y 3: clara -> clear
    site = tmp_path / 'server/data/music/.venv-heartmula/Lib/site-packages'
    assert (site / '__editable__.heartlib-0.1.0.pth').read_text() == str(
        tmp_path / 'server/data/music/models/heartlib'
    ) + '\n'
    url = json.loads((site / 'heartlib-0.1.0.dist-info/direct_url.json').read_text())['url']
    assert url == (tmp_path / 'server/data/music/models/heartlib').as_uri()


def test_second_run_says_already_migrated(tmp_path, capsys):
    tree(tmp_path)
    main(['--apply', '--root', str(tmp_path)])
    capsys.readouterr()
    assert main(['--apply', '--root', str(tmp_path)]) == 0
    assert 'already migrated' in capsys.readouterr().err


def test_collision_exits_1_without_move_nothing(tmp_path):
    tree(tmp_path)
    (tmp_path / 'server/data/narration/voz').mkdir(parents=True)
    (tmp_path / 'server/data/narration/voz/clara.wav').write_bytes(b'otro')
    assert main(['--apply', '--root', str(tmp_path)]) == 1
    assert (tmp_path / 'narration/voz/clara.wav').is_file() and (tmp_path / 'music/models/heartlib').is_dir()
    assert (tmp_path / 'server/data/narration/voz/clara.wav').read_bytes() == b'otro'


def test_merges_in_a_destination_that_already_has_versioned(tmp_path):
    """Tras el pull, server/data/narration/ ya tiene lo versionado: lo no versionado entra sin sobrescribir."""
    tree(tmp_path)
    (tmp_path / 'server/data/narration/docs').mkdir(parents=True)
    (tmp_path / 'server/data/narration/README.md').write_text('versionado')
    assert main(['--apply', '--root', str(tmp_path)]) == 0
    assert (tmp_path / 'server/data/narration/reference/default/clear.wav').is_file()
    assert (tmp_path / 'server/data/narration/README.md').read_text() == 'versionado'
    assert not (tmp_path / 'narration').exists()


def _tree_names(root):
    """Tras el paso 1: los datos ya están en server/data/narration/ con los nombres viejos."""
    data = root / 'server/data/narration'
    (data / 'voz/tomas').mkdir(parents=True)
    (data / 'voz/experta.wav').write_bytes(b'WAV1')
    (data / 'voz/experta.txt').write_bytes(b'texto')
    (data / 'voz/tomas/toma1.wav').write_bytes(b'TOMA')
    (data / 'voces').mkdir()
    (data / 'voces/catalogo.json').write_bytes(b'{"yesid": {}}')
    site = data / 'motores/index-tts/.venv/Lib/site-packages'
    site.mkdir(parents=True)
    (site / '__editable__.index_tts-0.1.pth').write_text(str(data / 'motores/index-tts') + '\n')
    (data / 'docs/guiones').mkdir(parents=True)
    (data / 'docs/guiones/guion.txt').write_bytes(b'guion')


def test_paso2_renames_with_the_same_bytes_and_rewrites_engines(tmp_path):
    _tree_names(tmp_path)
    assert main(['--apply', '--root', str(tmp_path)]) == 0
    data = tmp_path / 'server/data/narration'
    assert (data / 'reference/default/expert.wav').read_bytes() == b'WAV1'  # paso 2 y 3: perfil default
    assert (data / 'reference/default/expert.txt').read_bytes() == b'texto'
    assert (data / 'reference/default/takes/toma1.wav').read_bytes() == b'TOMA'
    assert (data / 'voices/catalog.json').read_bytes() == b'{"yesid": {}}'  # las claves las cambia git, no move-data
    assert (data / 'docs/scripts/guion.txt').read_bytes() == b'guion'
    assert not (data / 'voz').exists() and not (data / 'voces').exists() and not (data / 'docs/guiones').exists()
    assert not (data / 'motores').exists()
    pth = data / 'engines/index-tts/.venv/Lib/site-packages/__editable__.index_tts-0.1.pth'
    assert pth.read_text() == str(data / 'engines/index-tts') + '\n'


def test_paso2_is_idempotent(tmp_path, capsys):
    _tree_names(tmp_path)
    main(['--apply', '--root', str(tmp_path)])
    capsys.readouterr()
    assert main(['--apply', '--root', str(tmp_path)]) == 0
    assert 'already migrated' in capsys.readouterr().err
    assert (tmp_path / 'server/data/narration/reference/default/expert.wav').read_bytes() == b'WAV1'


def test_paso2_collision_exits_1_without_move_nothing(tmp_path):
    _tree_names(tmp_path)
    (tmp_path / 'server/data/narration/reference/default').mkdir(parents=True)
    (tmp_path / 'server/data/narration/reference/default/expert.wav').write_bytes(b'otro')
    assert main(['--apply', '--root', str(tmp_path)]) == 1
    data = tmp_path / 'server/data/narration'
    assert (data / 'voz/experta.wav').read_bytes() == b'WAV1'
    assert (data / 'voces/catalogo.json').is_file() and (data / 'motores/index-tts').is_dir()
    assert (data / 'reference/default/expert.wav').read_bytes() == b'otro'


def _tree_profile(root):
    """Tras el paso 2: las referencias ya tienen su nombre en inglés y todavía no hay perfil."""
    ref = root / 'server/data/narration/reference'
    (ref / 'takes/expert').mkdir(parents=True)
    (ref / 'expert.wav').write_bytes(b'WAV1')
    (ref / 'expert.txt').write_bytes(b'texto')
    (ref / 'takes/expert/2.wav').write_bytes(b'TOMA')


def test_paso3_moves_the_references_to_the_default_profile(tmp_path):
    _tree_profile(tmp_path)
    assert main(['--apply', '--root', str(tmp_path)]) == 0
    ref = tmp_path / 'server/data/narration/reference'
    assert (ref / 'default/expert.wav').read_bytes() == b'WAV1'
    assert (ref / 'default/expert.txt').read_bytes() == b'texto'
    assert (ref / 'default/takes/expert/2.wav').read_bytes() == b'TOMA'
    assert not (ref / 'expert.wav').exists()
    assert json.loads((ref / 'default/profile.json').read_text(encoding='utf-8'))['name'] == 'Mi voz'


def test_paso3_second_run_says_already_migrated(tmp_path, capsys):
    _tree_profile(tmp_path)
    main(['--apply', '--root', str(tmp_path)])
    capsys.readouterr()
    assert main(['--apply', '--root', str(tmp_path)]) == 0
    assert 'already migrated' in capsys.readouterr().err


def test_paso3_merges_into_a_default_that_already_has_versioned_text(tmp_path):
    """Tras el pull, git ya llevó los .txt versionados a reference/default/: los .wav entran sin tocar nada."""
    ref = tmp_path / 'server/data/narration/reference'
    (ref / 'default').mkdir(parents=True)
    (ref / 'default/expert.txt').write_bytes(b'versionado')
    (ref / 'expert.wav').write_bytes(b'WAV1')
    assert main(['--apply', '--root', str(tmp_path)]) == 0
    assert (ref / 'default/expert.wav').read_bytes() == b'WAV1'
    assert (ref / 'default/expert.txt').read_bytes() == b'versionado'


def test_paso3_collision_exits_1_without_moving_nothing(tmp_path):
    _tree_profile(tmp_path)
    ref = tmp_path / 'server/data/narration/reference'
    (ref / 'default').mkdir()
    (ref / 'default/expert.wav').write_bytes(b'otro')
    assert main(['--apply', '--root', str(tmp_path)]) == 1
    assert (ref / 'expert.wav').read_bytes() == b'WAV1' and (ref / 'takes/expert/2.wav').is_file()
    assert (ref / 'default/expert.wav').read_bytes() == b'otro'

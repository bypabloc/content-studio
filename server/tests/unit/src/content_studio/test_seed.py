"""Siembra de los datos de la app instalada (spec 022, D-3, AC-2): copiar lo que falta y nunca pisar lo del usuario."""

from __future__ import annotations

import json

from content_studio import seed
from content_studio.cli.main import main


def _source(root, version='0.1.0', clear='Lee esto con calma.'):
    (root / 'narration/reference/default').mkdir(parents=True, exist_ok=True)
    (root / 'narration/reference/default/clear.txt').write_text(clear, encoding='utf-8')
    (root / 'music').mkdir(exist_ok=True)
    (root / 'music/presets.txt').write_text('lofi', encoding='utf-8')
    (root / 'VERSION').write_text(version, encoding='utf-8')
    return root


def test_ac2_an_empty_home_gets_every_file_and_the_manifest(tmp_path):
    """Con la carpeta de datos vacía, se copia todo lo de seed/ (menos VERSION) y queda .seeded.json."""
    source, home = _source(tmp_path / 'seed'), tmp_path / 'home'

    result = seed.seed(source, home)

    assert result == {'version': '0.1.0', 'copied': 2, 'updated': 0, 'kept': 0}
    assert (home / 'narration/reference/default/clear.txt').read_text(encoding='utf-8') == 'Lee esto con calma.'
    manifest = json.loads((home / '.seeded.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '0.1.0'
    assert set(manifest['files']) == {'narration/reference/default/clear.txt', 'music/presets.txt'}
    assert not (home / 'VERSION').exists()


def test_ac2_seeding_again_changes_nothing(tmp_path):
    """La misma versión otra vez no copia nada: la siembra es idempotente."""
    source, home = _source(tmp_path / 'seed'), tmp_path / 'home'
    seed.seed(source, home)

    assert seed.seed(source, home) == {'version': '0.1.0', 'copied': 0, 'updated': 0, 'kept': 0}


def test_ac2_a_new_version_updates_untouched_files_and_leaves_a_new_copy_next_to_edited_ones(tmp_path):
    """Lo que el usuario no tocó se actualiza; lo que cambió queda igual, con <archivo>.new al lado."""
    home = tmp_path / 'home'
    seed.seed(_source(tmp_path / 'v1'), home)
    (home / 'music/presets.txt').write_text('mi lista', encoding='utf-8')
    v2 = _source(tmp_path / 'v2', version='0.2.0')
    (v2 / 'music/presets.txt').write_text('lofi y jazz', encoding='utf-8')
    (v2 / 'music/extra.txt').write_text('nuevo', encoding='utf-8')

    result = seed.seed(v2, home)

    assert result == {'version': '0.2.0', 'copied': 1, 'updated': 0, 'kept': 1}
    assert (home / 'music/presets.txt').read_text(encoding='utf-8') == 'mi lista'
    assert (home / 'music/presets.txt.new').read_text(encoding='utf-8') == 'lofi y jazz'
    assert (home / 'music/extra.txt').read_text(encoding='utf-8') == 'nuevo'


def test_ac2_an_untouched_file_takes_the_new_version(tmp_path):
    """Un archivo sembrado que nadie editó pasa al contenido nuevo."""
    home = tmp_path / 'home'
    seed.seed(_source(tmp_path / 'v1'), home)
    v2 = _source(tmp_path / 'v2', version='0.2.0')
    (v2 / 'music/presets.txt').write_text('lofi y jazz', encoding='utf-8')

    assert seed.seed(v2, home)['updated'] == 1
    assert (home / 'music/presets.txt').read_text(encoding='utf-8') == 'lofi y jazz'


def test_ac2_references_are_only_created_when_missing_and_other_profiles_are_never_touched(tmp_path):
    """reference/<perfil>/ es del usuario: un texto nuevo no reemplaza el suyo ni deja .new, y otro perfil no cambia."""
    home = tmp_path / 'home'
    seed.seed(_source(tmp_path / 'v1'), home)
    mine = home / 'narration/reference/mia/clear.wav'
    mine.parent.mkdir(parents=True)
    mine.write_bytes(b'mi voz')

    seed.seed(_source(tmp_path / 'v2', version='0.2.0', clear='Otro texto.'), home)

    assert (home / 'narration/reference/default/clear.txt').read_text(encoding='utf-8') == 'Lee esto con calma.'
    assert not (home / 'narration/reference/default/clear.txt.new').exists()
    assert mine.read_bytes() == b'mi voz'


def test_studio_seed_uses_the_resources_of_the_installed_app(tmp_path, monkeypatch, capsys):
    """`studio seed` siembra desde <recursos>/seed a la carpeta de datos; en un checkout no hay nada que sembrar."""
    resources, home = tmp_path / 'resources', tmp_path / 'home'
    _source(resources / 'seed')
    monkeypatch.setenv('CONTENT_STUDIO_HOME', str(home))
    monkeypatch.delenv('CONTENT_STUDIO_RESOURCES', raising=False)

    assert main(['seed']) == 0
    assert json.loads(capsys.readouterr().out) == {'skipped': 'not_installed'}

    monkeypatch.setenv('CONTENT_STUDIO_RESOURCES', str(resources))
    assert main(['seed']) == 0
    assert json.loads(capsys.readouterr().out)['copied'] == 2
    assert (home / 'music/presets.txt').is_file()

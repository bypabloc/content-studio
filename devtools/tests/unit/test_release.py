"""`python -m devtools release` (spec 022, D-7 y D-8, AC-6 y AC-10)."""

from __future__ import annotations

import json
import subprocess

from devtools import release


def _git(root, *args):
    subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)


def _repo(tmp_path, app_version='0.2.0'):
    conf = tmp_path / 'client/src-tauri/tauri.conf.json'
    conf.parent.mkdir(parents=True)
    conf.write_text(f'{{\n  "version": "{app_version}"\n}}\n', encoding='utf-8')
    _git(tmp_path, 'init', '-q')
    _git(tmp_path, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'feat: primera')
    _git(tmp_path, 'tag', 'v0.1.0')
    for subject in ('feat: instalador NSIS', 'fix: la cola no se pierde', 'docs: release.md', 'perf!: menos VRAM'):
        _git(tmp_path, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', subject)
    return tmp_path


def _installer(tmp_path, size=1024, signed=True):
    exe = tmp_path / 'bundle/nsis/Content Studio_0.2.0_x64-setup.exe'
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b'M' * size)
    if signed:
        exe.with_name(exe.name + '.sig').write_text('c2lnbmF0dXJl\n', encoding='utf-8')
    return exe


def test_notes_group_the_commits_since_the_previous_tag_and_add_the_windows_notice(tmp_path):
    """Solo los commits desde v0.1.0, por sección; docs no entra; el aviso de SmartScreen va siempre (D-8)."""
    root = _repo(tmp_path)

    text = release.notes(root, 'v0.2.0')

    assert '## Novedades\n\n- instalador NSIS\n' in text
    assert '## Correcciones\n\n- la cola no se pierde\n' in text
    assert '## Rendimiento\n\n- menos VRAM\n' in text
    assert 'primera' not in text
    assert 'release.md' not in text
    assert 'Ejecutar de todas formas' in text


def test_ac6_release_stages_the_installer_its_signature_latest_json_and_notes(tmp_path, capsys):
    """El instalador sin espacios en el nombre, la firma y un latest.json que apunta al asset del Release."""
    root = _repo(tmp_path)

    assert release.main(['--installer', str(_installer(tmp_path))], root) == 0

    staged = json.loads(capsys.readouterr().out)
    out = root / release.OUT
    name = 'Content-Studio_0.2.0_x64-setup.exe'
    assert staged['installer'] == f'{release.OUT}/{name}'
    assert (out / f'{name}.sig').is_file()
    manifest = json.loads((out / 'latest.json').read_text(encoding='utf-8'))
    assert manifest['version'] == '0.2.0'
    assert manifest['platforms']['windows-x86_64'] == {
        'signature': 'c2lnbmF0dXJl',
        'url': f'https://github.com/{release.REPO}/releases/download/v0.2.0/{name}',
    }
    assert manifest['notes'] == (out / 'notes.md').read_text(encoding='utf-8')


def test_ac10_a_dry_run_needs_no_signature_and_writes_no_latest_json(tmp_path, capsys):
    """En --dry-run (sin los secrets) arma el instalador y las notas, sin latest.json."""
    root = _repo(tmp_path)

    assert release.main(['--installer', str(_installer(tmp_path, signed=False)), '--dry-run'], root) == 0

    assert 'latest' not in json.loads(capsys.readouterr().out)
    assert not (root / release.OUT / 'latest.json').exists()


def test_without_dry_run_a_missing_signature_fails(tmp_path, capsys):
    """Sin la firma del updater no se publica: exit 1 y qué secret falta."""
    root = _repo(tmp_path)

    assert release.main(['--installer', str(_installer(tmp_path, signed=False))], root) == 1
    assert 'TAURI_SIGNING_PRIVATE_KEY' in capsys.readouterr().err


def test_ac6_an_installer_of_60_mb_or_more_fails(tmp_path, monkeypatch, capsys):
    """El límite de AC-6: el tamaño se mide antes de copiar nada."""
    root = _repo(tmp_path)
    monkeypatch.setattr(release, 'MAX_BYTES', 1000)

    assert release.main(['--installer', str(_installer(tmp_path, size=1000))], root) == 1
    assert 'the limit is 60 MB' in capsys.readouterr().err
    assert not (root / release.OUT).exists()


def test_a_missing_installer_is_exit_2(tmp_path, capsys):
    """Sin el .exe no hay nada que publicar."""
    assert release.main(['--installer', str(tmp_path / 'none.exe')], _repo(tmp_path)) == 2
    assert 'Run tauri build first' in capsys.readouterr().err


def test_notes_without_a_previous_tag_take_the_whole_history(tmp_path):
    """El primer Release: no hay tag anterior, así que entran todos los commits."""
    root = tmp_path
    (root / 'f').write_text('x', encoding='utf-8')
    _git(root, 'init', '-q')
    _git(root, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'feat: todo')

    assert '- todo' in release.notes(root, 'v0.1.0')

"""`python -m devtools bundle` y la configuración del instalador (spec 022, D-1 y D-5, AC-6)."""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
import zipfile

import pytest

from devtools import bundle, paths

TAURI = json.loads((paths.ROOT / 'client/src-tauri/tauri.conf.json').read_text(encoding='utf-8'))
# Los recursos van aparte: solo el build del instalador los suma (`tauri build --config src-tauri/tauri.bundle.json`).
BUNDLE = json.loads((paths.ROOT / 'client/src-tauri/tauri.bundle.json').read_text(encoding='utf-8'))


def _zip() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('uv.exe', b'MZ uv')
    return buffer.getvalue()


def _repo(tmp_path):
    files = {
        'pyproject.toml': '[tool.uv.workspace]\n',
        'uv.lock': 'version = 1\n',
        'server/pyproject.toml': '[project]\n',
        'server/src/content_studio/paths.py': 'ROOT = 1\n',
        'server/tests/test_x.py': 'def test(): ...\n',
        'server/data/narration/reference/default/clear.txt': 'Lee esto.\n',
        'client/src-tauri/tauri.conf.json': '{\n  "version": "0.3.0"\n}\n',
    }
    for rel, text in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding='utf-8')
    venv = tmp_path / 'server/data/narration/engines/.venv-x/python.exe'
    venv.parent.mkdir(parents=True)
    venv.write_bytes(b'no se versiona')
    subprocess.run(['git', 'init', '-q'], cwd=tmp_path, check=True)
    subprocess.run(['git', 'add', '--', *files], cwd=tmp_path, check=True)
    return tmp_path


def test_ac6_bundle_stages_the_tracked_server_the_lock_the_seed_and_a_verified_uv(tmp_path, monkeypatch, capsys):
    """app/ trae solo lo versionado (sin tests ni venvs), seed/ los textos con VERSION y bin/ el uv verificado."""
    root = _repo(tmp_path)
    data = _zip()
    monkeypatch.setattr(bundle, 'UV_SHA256', hashlib.sha256(data).hexdigest())

    assert bundle.main([], root, download=lambda url: data) == 0

    out = root / bundle.OUT
    assert json.loads(capsys.readouterr().out) == {'app': 5, 'seed': 1, 'uv': f'{bundle.OUT}/bin/uv.exe'}
    assert (out / 'app/server/src/content_studio/paths.py').is_file()
    assert (out / 'app/uv.lock').is_file()
    assert not (out / 'app/server/tests').exists()
    assert not (out / 'app/server/data/narration/engines').exists()
    assert (out / 'seed/narration/reference/default/clear.txt').read_text(encoding='utf-8') == 'Lee esto.\n'
    assert (out / 'seed/VERSION').read_text(encoding='utf-8') == '0.3.0'
    assert (out / 'bin/uv.exe').read_bytes() == b'MZ uv'
    assert (root / 'tmp/bundle' / f'uv-{bundle.UV_VERSION}.zip').is_file()


def test_ac6_a_uv_download_with_another_hash_is_refused(tmp_path, capsys):
    """Un zip que no es el fijado no se abre: exit 2 y el motivo."""
    root = _repo(tmp_path)

    assert bundle.main([], root, download=lambda url: _zip()) == 2
    assert 'the download was altered' in capsys.readouterr().err
    assert not (root / bundle.OUT / 'bin/uv.exe').exists()


def test_bundle_takes_no_arguments_and_needs_git(tmp_path, capsys):
    """Un argumento de más es exit 2; fuera de un repo, git falla y también."""
    assert bundle.main(['--x'], tmp_path) == 2
    with pytest.raises(bundle.BundleError):
        bundle.tracked(tmp_path, 'server')


def test_ac6_the_installer_is_nsis_per_user_in_spanish_with_the_staged_resources():
    """tauri.conf.json: NSIS por usuario (sin admin), en español, con app/, seed/ y bin/ desde bundle/."""
    config = TAURI['bundle']
    nsis = config['windows']['nsis']
    assert config['targets'] == ['nsis']
    assert nsis['installMode'] == 'currentUser'
    assert nsis['languages'] == ['Spanish']
    assert nsis['installerHooks'] == 'installer/nsis/hooks.nsh'
    assert 'resources' not in config  # cargo check y tauri dev no necesitan los recursos armados
    assert BUNDLE['bundle']['resources'] == {'bundle/app/': 'app/', 'bundle/seed/': 'seed/', 'bundle/bin/': 'bin/'}
    assert (paths.ROOT / 'client/src-tauri' / nsis['installerHooks']).is_file()

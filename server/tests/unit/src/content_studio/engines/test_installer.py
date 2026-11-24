"""Instalación reanudable sin dependencias remotas, AC-3 y AC-4 de la spec 012."""

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from content_studio.engines import installer
from content_studio.engines.recipes import Recipe


def _fake_recipe():
    return Recipe(
        'fake',
        'narration',
        4.8,
        0,
        True,
        'MIT',
        ({'kind': 'python', 'version': '3.12'}, {'kind': 'venv', 'path': '.venv'}, {'kind': 'verify'}),
    )


def test_ac3_retries_skip_completed_steps_and_record_the_owner(tmp_path, monkeypatch):
    """Cada paso es un proceso real de Python que solo escribe datos en tmp_path."""
    try:
        from content_studio.engines import installer
    except ImportError as error:
        pytest.fail(f'AC-3 requires the resumable installer: {error}')
    monkeypatch.setattr(installer.shutil, 'disk_usage', lambda path: SimpleNamespace(free=10**10))
    calls = []
    successful = []

    def execute(step, recipe, location, cache, report):
        kind = step['kind']
        calls.append(kind)
        fail = calls.count(kind) == 1 and kind == 'venv'
        subprocess.run([sys.executable, '-c', 'import sys; sys.exit(int(sys.argv[1]))', str(int(fail))], check=True)
        successful.append(kind)

    monkeypatch.setattr(installer, 'execute_step', execute)
    with pytest.raises(subprocess.CalledProcessError):
        installer.install(_fake_recipe(), tmp_path)
    assert successful == ['python']

    result = installer.install(_fake_recipe(), tmp_path)

    assert calls == ['python', 'venv', 'venv', 'verify']
    assert successful == ['python', 'venv', 'verify']
    manifest = json.loads((tmp_path / 'fake' / 'install.json').read_text(encoding='utf-8'))
    assert manifest == result
    assert manifest['owner'] == 'app'


def test_ac4_checks_space_before_executing_a_step(tmp_path, monkeypatch):
    """La reserva de disco se comprueba antes de instalar Python o descargar pesos."""
    try:
        from content_studio.engines import installer
    except ImportError as error:
        pytest.fail(f'AC-4 requires the disk check: {error}')
    monkeypatch.setattr(installer.shutil, 'disk_usage', lambda path: SimpleNamespace(free=10**9))

    with pytest.raises(installer.InstallError) as error:
        installer.install(_fake_recipe(), tmp_path)

    assert error.value.code == 'disk_full'
    assert not (tmp_path / 'fake').exists()


def test_download_byte_progress_stays_inside_its_step(tmp_path, monkeypatch):
    """El avance por bytes ocupa el tramo global asignado al paso HF."""
    from content_studio.engines import installer

    recipe = Recipe(
        'fake',
        'narration',
        4.8,
        0,
        True,
        'MIT',
        ({'kind': 'python'}, {'kind': 'hf'}, {'kind': 'verify'}),
    )
    monkeypatch.setattr(installer.shutil, 'disk_usage', lambda path: SimpleNamespace(free=10**10))
    emitted = []
    monkeypatch.setattr(installer.progress, 'emit', lambda p, stage: emitted.append((p, stage)))

    spans = []

    def execute(step, selected, home, cache, span):
        spans.append(span)
        if step['kind'] == 'hf':
            installer.progress.emit(round(span[0] + (span[1] - span[0]) * 0.5, 4), '4/8 bytes')

    monkeypatch.setattr(installer, 'execute_step', execute)
    installer.install(recipe, tmp_path)

    byte_progress = next(item for item in emitted if item[1] == '4/8 bytes')
    assert byte_progress == (0.5, '4/8 bytes')
    assert spans[1] == (1 / 3, 2 / 3)
    assert [value for value, _ in emitted] == sorted(value for value, _ in emitted)


def test_read_manifest_rejects_missing_invalid_and_non_object_data(tmp_path):
    home = tmp_path / 'fake'
    assert installer.read_manifest(home) == {}
    home.mkdir()
    manifest = home / 'install.json'
    manifest.write_text('{', encoding='utf-8')
    assert installer.read_manifest(home) == {}
    manifest.write_text('[]', encoding='utf-8')
    assert installer.read_manifest(home) == {}


def test_owned_paths_reject_a_path_that_resolves_outside_the_root(tmp_path, monkeypatch):
    path_type = type(tmp_path)
    original_resolve = path_type.resolve
    escaped = tmp_path / 'fake'

    def resolve(path, *args, **kwargs):
        if path == escaped:
            return tmp_path / 'user-data'
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(path_type, 'resolve', resolve)
    with pytest.raises(installer.InstallError, match='engine_external'):
        installer._owned_paths(tmp_path, 'fake')


@pytest.mark.parametrize(
    'manifest',
    [{'owner': 'app', 'paths': '../user-data'}, {'owner': 'app', 'paths': ['../user-data']}],
)
def test_uninstall_rejects_unlisted_paths_without_deleting_user_data(tmp_path, manifest):
    home = tmp_path / 'qwen-0.6b'
    user_data = tmp_path / 'user-data'
    home.mkdir()
    user_data.mkdir()
    (home / 'install.json').write_text(json.dumps(manifest), encoding='utf-8')
    (user_data / 'keep').write_bytes(b'protected')

    with pytest.raises(installer.InstallError, match='engine_external'):
        installer.remove_paths(tmp_path, 'qwen-0.6b', manifest)

    assert (user_data / 'keep').read_bytes() == b'protected'
    assert home.exists()


def test_uninstall_reports_when_the_engine_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(installer, 'engine_venv', lambda recipe, root: tmp_path / 'missing-venv')
    with pytest.raises(installer.InstallError, match='engine_not_installed'):
        installer.uninstall('qwen-0.6b', tmp_path)


def test_install_is_idempotent_for_an_existing_matching_manifest(tmp_path, monkeypatch):
    home = tmp_path / 'fake'
    home.mkdir()
    existing = {'owner': 'app', 'recipe_version': 1, 'paths': ['fake']}
    (home / 'install.json').write_text(json.dumps(existing), encoding='utf-8')
    monkeypatch.setattr(installer, 'execute_step', lambda *args: pytest.fail('idempotent install ran a step'))

    assert installer.install(_fake_recipe(), tmp_path) == existing


def test_install_rejects_existing_data_without_an_app_manifest(tmp_path):
    home = tmp_path / 'fake'
    home.mkdir()
    (home / 'keep').write_text('user data', encoding='utf-8')

    with pytest.raises(installer.InstallError, match='engine_external'):
        installer.install(_fake_recipe(), tmp_path)

    assert (home / 'keep').read_text(encoding='utf-8') == 'user data'


def test_install_rejects_existing_cache_without_an_app_manifest(tmp_path):
    cache = tmp_path / 'hf' / 'fake'
    cache.mkdir(parents=True)
    (cache / 'keep').write_bytes(b'user weights')

    with pytest.raises(installer.InstallError, match='engine_external'):
        installer.install(_fake_recipe(), tmp_path)

    assert (cache / 'keep').read_bytes() == b'user weights'


def test_repair_rejects_external_installation(tmp_path):
    with pytest.raises(installer.InstallError, match='engine_external'):
        installer.install(_fake_recipe(), tmp_path, repair=True)


def test_repair_rebuilds_the_venv_and_preserves_weights(tmp_path, monkeypatch):
    recipe = Recipe(
        'fake',
        'narration',
        4.8,
        0,
        True,
        'MIT',
        ({'kind': 'python', 'version': '3.12'}, {'kind': 'venv', 'path': '.venv'}, {'kind': 'hf'}, {'kind': 'verify'}),
    )
    home = tmp_path / recipe.engine
    family = home / recipe.family
    venv = family / recipe.venv
    markers = home / 'steps'
    cache = tmp_path / 'hf' / recipe.engine
    venv.mkdir(parents=True)
    markers.mkdir()
    cache.mkdir(parents=True)
    (venv / 'old').write_text('old', encoding='utf-8')
    (cache / 'weights').write_bytes(b'keep')
    (home / 'install.json').write_text(json.dumps({'owner': 'app', 'recipe_version': 0}), encoding='utf-8')
    for index in range(len(recipe.steps)):
        (markers / f'{recipe.version}-{index}.done').touch()
    monkeypatch.setattr(installer.shutil, 'disk_usage', lambda path: SimpleNamespace(free=10**10))
    original_rmtree = installer.shutil.rmtree

    def rmtree(path, onerror=None):
        if path == venv:
            if onerror is None:
                raise FileNotFoundError(path / 'vanished')
            error = FileNotFoundError(path / 'vanished')
            onerror(os.unlink, str(path / 'vanished'), (FileNotFoundError, error, None))
        original_rmtree(path)

    monkeypatch.setattr(installer.shutil, 'rmtree', rmtree)
    called = []
    monkeypatch.setattr(installer, 'execute_step', lambda step, *args: called.append(step['kind']))

    installer.install(recipe, tmp_path, repair=True)

    assert called == ['python', 'venv', 'verify']
    assert (markers / f'{recipe.version}-2.done').is_file()
    assert not (venv / 'old').exists()
    assert (cache / 'weights').read_bytes() == b'keep'


def test_rmtree_propagates_errors_other_than_missing_files(tmp_path, monkeypatch):
    def rmtree(path, onerror):
        error = PermissionError('denied')
        onerror(os.unlink, str(path), (PermissionError, error, None))

    monkeypatch.setattr(installer.shutil, 'rmtree', rmtree)

    with pytest.raises(PermissionError, match='denied'):
        installer._rmtree_missing_ok(tmp_path)


def test_rmtree_handles_a_child_beyond_windows_max_path(tmp_path):
    filename = 'header_' + 'x' * 40 + '.h'
    parent_length = len(str(tmp_path.resolve()))
    target = tmp_path / ('n' * max(1, 220 - parent_length - 1))
    target.mkdir()
    absolute_target = str(target.resolve())
    child_path = absolute_target + '\\' + filename
    assert len(child_path) > 260

    if os.name == 'nt':
        if absolute_target.startswith('\\\\'):
            absolute_target = '\\\\?\\UNC\\' + absolute_target[2:]
        else:
            absolute_target = '\\\\?\\' + absolute_target
        child_path = absolute_target + '\\' + filename
    Path(child_path).write_bytes(b'header')

    installer._rmtree_missing_ok(target)

    assert not target.exists()


def test_repair_rejects_a_venv_that_resolves_outside_its_family(tmp_path, monkeypatch):
    recipe = _fake_recipe()
    home = tmp_path / recipe.engine
    family = home / recipe.family
    venv = family / recipe.venv
    venv.mkdir(parents=True)
    (home / 'install.json').write_text(json.dumps({'owner': 'app'}), encoding='utf-8')
    path_type = type(tmp_path)
    original_resolve = path_type.resolve

    def resolve(path, *args, **kwargs):
        if path == venv:
            return tmp_path / 'outside-venv'
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(path_type, 'resolve', resolve)
    monkeypatch.setattr(installer.shutil, 'disk_usage', lambda path: SimpleNamespace(free=10**10))

    with pytest.raises(installer.InstallError, match='engine_external'):
        installer.install(recipe, tmp_path, repair=True)


def test_managed_ready_requires_a_python_executable_and_no_pending_marker(tmp_path, monkeypatch):
    recipe = _fake_recipe()
    interpreter = tmp_path / 'python.exe'
    monkeypatch.setattr(installer.process, 'python_de', lambda venv: interpreter)
    assert not installer.managed_ready(recipe, tmp_path)
    base = tmp_path / recipe.engine
    base.mkdir()
    interpreter.touch()
    (base / 'installing.json').touch()
    assert not installer.managed_ready(recipe, tmp_path)
    (base / 'installing.json').unlink()
    assert installer.managed_ready(recipe, tmp_path)


def test_commercial_and_license_requirements_follow_the_engine_registry(monkeypatch):
    assert installer.commercial('qwen-0.6b')
    assert installer.commercial('unknown-engine')
    assert not installer.commercial('omnivoice')
    monkeypatch.setattr(installer.settings, 'get', lambda conn, key: False)
    with pytest.raises(installer.InstallError, match='engine_license_required'):
        installer.check_license(None, 'omnivoice')
    monkeypatch.setattr(installer.settings, 'get', lambda conn, key: True)
    installer.check_license(None, 'omnivoice')


def test_list_engines_reports_active_owned_partial_external_and_missing_states(tmp_path, monkeypatch):
    names = ('qwen-0.6b', 'voxcpm2', 'omnivoice', 'chatterbox', 'cosyvoice3', 'indextts')
    selected = [
        Recipe(
            name,
            'narration',
            1,
            2,
            True,
            'MIT',
            ({'kind': 'python', 'version': '3.12'}, {'kind': 'venv', 'path': '.venv'}),
        )
        for name in names
    ]
    root = tmp_path / 'engines'
    (root / 'voxcpm2').mkdir(parents=True)
    (root / 'voxcpm2' / 'install.json').write_text(json.dumps({'owner': 'app', 'size_bytes': 7}), encoding='utf-8')
    (root / 'omnivoice').mkdir(parents=True)
    (root / 'omnivoice' / 'install.json').write_text(json.dumps({'owner': 'app', 'size_bytes': 9}), encoding='utf-8')
    (root / 'cosyvoice3').mkdir(parents=True)
    (root / 'cosyvoice3' / 'installing.json').touch()
    external = tmp_path / 'external' / '.venv'
    external.mkdir(parents=True)
    (external / 'model.bin').write_bytes(b'weight')
    monkeypatch.setattr(installer.recipes, 'load_all', lambda: selected)
    monkeypatch.setattr(
        installer.jobs,
        'list_jobs',
        lambda conn, kind: [
            {'params': {'engine': names[0]}, 'id': 4, 'status': 'running'},
            {'params': {'engine': names[2]}, 'id': 5, 'status': 'error'},
        ],
    )
    monkeypatch.setattr(installer.settings, 'get', lambda conn, key: {'ok': False} if names[2] in key else None)
    monkeypatch.setattr(
        installer,
        'engine_venv',
        lambda recipe, base: external if recipe.engine == names[3] else base / recipe.engine / '.venv',
    )
    monkeypatch.setattr(installer, 'managed_ready', lambda recipe, base: recipe.engine == names[1])

    entries = installer.list_engines(None, root)

    assert [entry['status'] for entry in entries] == [
        'installing',
        'installed',
        'broken',
        'external',
        'broken',
        'missing',
    ]
    assert entries[3]['owner'] == 'external'
    assert entries[1]['size_bytes'] == 7
    assert entries[2]['size_bytes'] == 9


def test_force_removes_only_the_known_external_venv_and_preserves_shared_data(tmp_path, monkeypatch):
    external = tmp_path / 'narration'
    venv = external / '.venv-qwen'
    managed = tmp_path / 'managed'
    cache = managed / 'hf' / 'qwen-0.6b'
    venv.mkdir(parents=True)
    cache.mkdir(parents=True)
    (venv / 'python.exe').write_bytes(b'venv')
    (external / 'reference.wav').write_bytes(b'reference')
    (cache / 'weights.bin').write_bytes(b'model')
    monkeypatch.setattr(installer.paths, 'NARRATION', external)
    monkeypatch.setattr(installer.paths, 'MUSIC', tmp_path / 'music')

    installer.uninstall('qwen-0.6b', managed, force=True)

    assert not venv.exists()
    assert (external / 'reference.wav').read_bytes() == b'reference'
    assert (cache / 'weights.bin').read_bytes() == b'model'


def test_force_does_not_bypass_manifest_path_ownership(tmp_path):
    home = tmp_path / 'qwen-0.6b'
    user_data = tmp_path / 'user-data'
    home.mkdir()
    user_data.mkdir()
    (user_data / 'keep').write_bytes(b'protected')
    manifest = {'owner': 'app', 'paths': ['../user-data']}
    (home / 'install.json').write_text(json.dumps(manifest), encoding='utf-8')

    with pytest.raises(installer.InstallError, match='engine_external'):
        installer.uninstall('qwen-0.6b', tmp_path, force=True)

    assert (user_data / 'keep').read_bytes() == b'protected'


def _zip_bytes():
    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('llama-server.exe', b'binary')
    return buffer.getvalue()


def _serve_bytes(monkeypatch, payload):
    import io

    from content_studio.engines import steps

    class Response(io.BytesIO):
        headers = {'Content-Length': str(len(payload))}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    monkeypatch.setattr(steps.urllib.request, 'urlopen', lambda url, timeout: Response(payload))


def _download_recipe(sha256):
    step = {'kind': 'download', 'url': 'https://example.com/llama.zip', 'sha256': sha256, 'extract': 'bin'}
    return Recipe('fake', 'assistant', 0.1, 0, False, 'MIT', (step,))


def test_ac1_checksum_mismatch_aborts_without_extracting(tmp_path, monkeypatch):
    """Spec 021 AC-1: un sha256 distinto aborta con checksum_mismatch y no deja el zip ni lo extraído."""
    monkeypatch.setattr(installer.shutil, 'disk_usage', lambda path: SimpleNamespace(free=10**10))
    _serve_bytes(monkeypatch, _zip_bytes())

    with pytest.raises(installer.InstallError) as error:
        installer.install(_download_recipe('0' * 64), tmp_path)

    assert error.value.code == 'checksum_mismatch'
    assert installer.EXIT_CODES['checksum_mismatch']
    assert not (tmp_path / 'fake' / 'assistant' / 'bin').exists()
    assert not list((tmp_path / 'hf').rglob('*.zip'))


def test_ac1_matching_checksum_extracts_into_the_engine_folder(tmp_path, monkeypatch):
    """Con el sha256 correcto, el zip se extrae en la carpeta del motor y no queda en la caché."""
    import hashlib

    payload = _zip_bytes()
    monkeypatch.setattr(installer.shutil, 'disk_usage', lambda path: SimpleNamespace(free=10**10))
    _serve_bytes(monkeypatch, payload)

    installer.install(_download_recipe(hashlib.sha256(payload).hexdigest()), tmp_path)

    assert (tmp_path / 'fake' / 'assistant' / 'bin' / 'llama-server.exe').read_bytes() == b'binary'
    assert not list((tmp_path / 'hf').rglob('*.zip'))

"""Progreso y ejecución de los pasos de receta, AC-3 de la spec 012."""

import json
import sys
import threading
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

from content_studio.engines import steps
from content_studio.engines.recipes import Recipe


def _recipe():
    return Recipe(
        'fake',
        'narration',
        1,
        0,
        True,
        'MIT',
        ({'kind': 'python', 'version': '3.12'}, {'kind': 'venv', 'path': '.venv'}),
    )


def test_download_reports_bytes_without_network(tmp_path, monkeypatch):
    """El monitor informa los bytes escritos por la descarga simulada."""
    downloaded = threading.Event()

    class StopEvent:
        def __init__(self):
            self.waits = 0

        def wait(self, timeout=None):
            self.waits += 1
            if self.waits == 1:
                downloaded.wait()
                return False
            return True

        def set(self):
            downloaded.set()

    observers = []

    class Observer:
        def __init__(self, target, daemon):
            self.target = target
            observers.append(self)

        def start(self):
            pass

        def join(self):
            pass

    hub = ModuleType('huggingface_hub')
    hub.HfApi = lambda: SimpleNamespace(
        model_info=lambda *args, **kwargs: SimpleNamespace(siblings=[SimpleNamespace(rfilename='weights.bin', size=8)])
    )

    def snapshot_download(repo, revision, cache_dir, **kwargs):
        target = Path(cache_dir) / 'models--org--model' / 'blobs' / 'weights.bin'
        target.parent.mkdir(parents=True)
        target.write_bytes(b'12')
        downloaded.set()
        observers[0].target()

    hub.snapshot_download = snapshot_download
    monkeypatch.setitem(sys.modules, 'huggingface_hub', hub)
    monkeypatch.setattr(steps.threading, 'Event', StopEvent)
    monkeypatch.setattr(steps.threading, 'Thread', Observer)
    emitted = []
    monkeypatch.setattr(steps.progress, 'emit', lambda p, stage: emitted.append((p, stage)))
    monkeypatch.setenv('HF_HOME', str(tmp_path))
    monkeypatch.setenv('CONTENT_STUDIO_PROGRESS_START', str(1 / 3))
    monkeypatch.setenv('CONTENT_STUDIO_PROGRESS_END', str(2 / 3))

    steps._download({'repo': 'org/model', 'revision': 'abc', 'into': 'hf'})

    assert '2/8 bytes' in (stage for _, stage in emitted)
    assert next(item for item in emitted if item[1] == '2/8 bytes') == (0.4167, '2/8 bytes')


def test_run_executes_a_checked_command(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(steps.subprocess, 'run', lambda *args, **kwargs: calls.append((args, kwargs)))

    steps._run(['tool', '--version'], {'PATH': 'bin'}, tmp_path)

    assert calls[0][0] == (['tool', '--version'],)
    assert calls[0][1] == {'cwd': tmp_path, 'env': {'PATH': 'bin'}, 'stdin': steps.subprocess.DEVNULL, 'check': True}


def test_pip_builds_optional_arguments_and_filtered_requirements(monkeypatch, tmp_path):
    requirements = tmp_path / 'requirements.txt'
    requirements.write_text('torch==2.0\n numpy==1.0\nscipy==1.1\n', encoding='utf-8')
    calls = []
    monkeypatch.setattr(steps, '_run', lambda command, env, home: calls.append(command))
    selected = {
        'uninstall': True,
        'index': 'https://packages.invalid/simple',
        'torch_backend': 'cu128',
        'no_deps': True,
        'editable': 'engine',
        'requirements': 'requirements.txt',
        'exclude': ['torch', 'numpy'],
        'packages': ['extra'],
    }

    steps._pip(selected, tmp_path, tmp_path / 'python.exe', {})

    command = calls[0]
    assert command[:9] == [
        'uv',
        'pip',
        'uninstall',
        '--python',
        str(tmp_path / 'python.exe'),
        '--index-url',
        'https://packages.invalid/simple',
        '--torch-backend',
        'cu128',
    ]
    assert '--no-deps' in command
    assert command[command.index('--editable') + 1] == str(tmp_path / 'engine')
    assert (tmp_path / 'requirements-install.txt').read_text(encoding='utf-8') == 'scipy==1.1'
    assert command[-1] == 'extra'


def test_pip_uses_default_install_without_optional_arguments(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(steps, '_run', lambda command, env, home: calls.append(command))

    steps._pip({'packages': ['package']}, tmp_path, tmp_path / 'python.exe', {})

    assert calls == [['uv', 'pip', 'install', '--python', str(tmp_path / 'python.exe'), 'package']]


def test_git_pins_commit_and_updates_submodules_only_when_requested(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(steps, '_run', lambda command, env, home: calls.append(command))
    step = {
        'into': 'repo',
        'url': 'https://example.invalid/project.git',
        'commit': 'abc123',
        'recursive': True,
    }

    steps._git(step, tmp_path, {})

    repo = str(tmp_path / 'repo')
    assert calls == [
        ['git', 'init', repo],
        ['git', '-C', repo, 'fetch', '--depth', '1', step['url'], 'abc123'],
        ['git', '-C', repo, 'checkout', '--detach', 'abc123'],
        ['git', '-C', repo, 'submodule', 'update', '--init', '--recursive', '--depth', '1'],
    ]


def test_execute_step_routes_each_recipe_kind(monkeypatch, tmp_path):
    home, cache = tmp_path / 'engine', tmp_path / 'hf'
    commands, delegated = [], []
    monkeypatch.setenv('PYTHONPATH', 'existing')
    monkeypatch.setattr(steps.process, 'python_de', lambda venv: venv / 'python.exe')
    monkeypatch.setattr(steps.process, 'env_src', lambda env: env)
    monkeypatch.setattr(steps, '_run', lambda command, env, cwd: commands.append((command, env, cwd)))
    monkeypatch.setattr(steps, '_pip', lambda *args: delegated.append(('pip', args)))
    monkeypatch.setattr(steps, '_git', lambda *args: delegated.append(('git', args)))
    recipe = _recipe()
    span = (0.25, 0.5)
    selected = [
        {'kind': 'python', 'version': '3.12'},
        {'kind': 'venv'},
        {'kind': 'pip'},
        {'kind': 'git'},
        {'kind': 'verify', 'import': 'module'},
        {'kind': 'verify', 'import': 'module', 'paths': ['repo/src']},
        {'kind': 'hf', 'repo': 'org/model', 'revision': 'abc', 'into': 'hf'},
    ]

    for step in selected:
        steps.execute_step(step, recipe, home, cache, span)

    assert commands[0][0] == ['uv', 'python', 'install', '3.12']
    assert commands[1][0][:5] == ['uv', 'venv', '--allow-existing', '--python', '3.12']
    assert delegated[0][0] == 'pip'
    assert delegated[1][0] == 'git'
    assert commands[2][0][1:3] == ['-c', 'import importlib, sys; importlib.import_module(sys.argv[1])']
    assert commands[2][1]['PYTHONPATH'] == 'existing'
    assert commands[3][1]['PYTHONPATH'].startswith(str(home / 'repo/src'))
    assert commands[4][0][1:3] == ['-m', 'content_studio.engines.steps']
    assert commands[4][1]['CONTENT_STUDIO_PROGRESS_START'] == '0.25'
    assert commands[4][1]['CONTENT_STUDIO_PROGRESS_END'] == '0.5'


def test_file_bytes_skips_files_removed_during_download(tmp_path, monkeypatch):
    stable, missing = tmp_path / 'stable.bin', tmp_path / 'missing.bin'
    stable.write_bytes(b'123')
    missing.write_bytes(b'123456')
    original_is_file, original_stat = Path.is_file, Path.stat

    def is_file(path):
        return True if path == missing else original_is_file(path)

    def stat(path, *args, **kwargs):
        if path == missing:
            raise FileNotFoundError(path)
        return original_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'is_file', is_file)
    monkeypatch.setattr(Path, 'stat', stat)

    assert steps._file_bytes(tmp_path) == 3


def test_file_bytes_skips_directories_removed_during_scan(tmp_path, monkeypatch):
    stable = tmp_path / 'stable.bin'
    stable.write_bytes(b'123')
    vanishing = tmp_path / 'vanishing'
    vanishing.mkdir()
    original_scandir = steps.os.scandir

    def scandir(folder):
        if Path(folder) == vanishing:
            raise FileNotFoundError(folder)
        return original_scandir(folder)

    monkeypatch.setattr(steps.os, 'scandir', scandir)

    assert steps._file_bytes(tmp_path) == 3


def test_file_bytes_propagates_directory_scan_errors(tmp_path, monkeypatch):
    def scandir(_):
        raise PermissionError('denied')

    monkeypatch.setattr(steps.os, 'scandir', scandir)

    with pytest.raises(PermissionError, match='denied'):
        steps._file_bytes(tmp_path)


def test_download_uses_local_directory_and_filters_patterns(monkeypatch, tmp_path):
    hub = ModuleType('huggingface_hub')
    seen = {}
    hub.HfApi = lambda: SimpleNamespace(
        model_info=lambda repo, revision, files_metadata: SimpleNamespace(
            siblings=[
                SimpleNamespace(rfilename='allowed.bin', size=8),
                SimpleNamespace(rfilename='ignored.bin', size=4),
                SimpleNamespace(rfilename='other.txt', size=2),
            ]
        )
    )

    def snapshot_download(repo, revision, cache_dir, local_dir, allow_patterns, ignore_patterns):
        seen.update(locals())
        Path(local_dir).mkdir(parents=True)

    hub.snapshot_download = snapshot_download

    class Observer:
        def __init__(self, target, daemon):
            pass

        def start(self):
            pass

        def join(self):
            pass

    monkeypatch.setitem(sys.modules, 'huggingface_hub', hub)
    monkeypatch.setattr(steps.threading, 'Thread', Observer)
    monkeypatch.setattr(steps.progress, 'emit', lambda p, stage: None)
    monkeypatch.setenv('HF_HOME', str(tmp_path / 'cache'))
    local = tmp_path / 'model-files'

    steps._download(
        {
            'repo': 'org/model',
            'revision': 'abc',
            'into': str(local),
            'allow_patterns': ['*.bin'],
            'ignore_patterns': ['ignored*'],
        }
    )

    assert seen['local_dir'] == local
    assert seen['allow_patterns'] == ['*.bin']
    assert seen['ignore_patterns'] == ['ignored*']
    assert not (tmp_path / 'cache' / 'hub' / 'models--org--model' / 'refs' / 'main').exists()


def test_ac2_token_en_env_no_en_argv(monkeypatch, tmp_path):
    """AC-2 (spec 034): HF_TOKEN llega solo al entorno de un paso gated; argv y los demás pasos no lo reciben."""
    calls = []
    monkeypatch.setattr(steps.process, 'python_de', lambda venv: Path(sys.executable))
    monkeypatch.setattr(steps, '_run', lambda command, env, cwd: calls.append((command, env)))
    monkeypatch.setenv('HF_TOKEN', 'hf_heredado_que_no_debe_viajar')
    gated = {'kind': 'hf', 'repo': 'owner/model', 'revision': '0' * 40, 'into': 'hf', 'gated': True}
    plain = {'kind': 'pip', 'packages': ['torch==2.11.0+cu128']}

    steps.execute_step(gated, _recipe(), tmp_path, tmp_path / 'cache', (0, 1), token='hf_secreto_1234567890abcdef')
    steps.execute_step(plain, _recipe(), tmp_path, tmp_path / 'cache', (0, 1), token='hf_secreto_1234567890abcdef')

    (gated_command, gated_env), (plain_command, plain_env) = calls
    assert gated_env['HF_TOKEN'] == 'hf_secreto_1234567890abcdef'
    assert not any(
        'hf_secreto_1234567890abcdef' in part or 'hf_heredado' in part for part in gated_command + plain_command
    )
    assert 'HF_TOKEN' not in plain_env


def test_ac3_gated_repo_exits_25(monkeypatch, capsys):
    """AC-3 (spec 034): un 401 o 403 de Hugging Face sale con 25 y el mensaje no muestra el token."""
    errors = ModuleType('huggingface_hub.errors')

    class HfHubHTTPError(Exception):
        def __init__(self, status):
            super().__init__('denied')
            self.response = SimpleNamespace(status_code=status)

    errors.HfHubHTTPError = HfHubHTTPError
    monkeypatch.setitem(sys.modules, 'huggingface_hub', ModuleType('huggingface_hub'))
    monkeypatch.setitem(sys.modules, 'huggingface_hub.errors', errors)
    monkeypatch.setenv('HF_TOKEN', 'hf_secreto_1234567890abcdef')
    step = {'repo': 'pyannote/speaker-diarization-community-1', 'revision': 'x', 'into': 'models/community-1'}

    for status in (401, 403):

        def denied(_step, status=status):
            raise HfHubHTTPError(status)

        monkeypatch.setattr(steps, '_download', denied)
        code = steps._run_hf_step(json.dumps(step))
        err = capsys.readouterr().err
        assert code == 25
        assert 'Access denied to pyannote/speaker-diarization-community-1' in err
        assert 'hf_secreto_1234567890abcdef' not in err

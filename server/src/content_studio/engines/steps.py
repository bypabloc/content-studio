"""Comandos de una receta. Cada paso se ejecuta con argumentos separados."""

from __future__ import annotations

import fnmatch
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

from content_studio.common import process, progress
from content_studio.engines.recipes import Recipe


def _run(command: list[str], env: dict[str, str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL, check=True)


def _pip(step: dict, home: Path, python: Path, env: dict[str, str]) -> None:
    action = 'uninstall' if step.get('uninstall') else 'install'
    command = ['uv', 'pip', action, '--python', str(python)]
    if step.get('index'):
        command += ['--index-url', step['index']]
    if step.get('torch_backend'):
        command += ['--torch-backend', step['torch_backend']]
    if step.get('no_deps'):
        command.append('--no-deps')
    if step.get('editable'):
        command += ['--editable', str(home / step['editable'])]
    if step.get('requirements'):
        requirements = home / step['requirements']
        if step.get('exclude'):
            source = requirements.read_text(encoding='utf-8').splitlines()
            filtered = home / 'requirements-install.txt'
            prefixes = tuple(prefix.lower() for prefix in step['exclude'])
            filtered.write_text(
                '\n'.join(line for line in source if not line.lstrip().lower().startswith(prefixes)),
                encoding='utf-8',
            )
            requirements = filtered
        command += ['--requirement', str(requirements)]
    _run(command + step['packages'], env, home)


def _git(step: dict, home: Path, env: dict[str, str]) -> None:
    repo = home / step['into']
    repo.mkdir(parents=True, exist_ok=True)
    _run(['git', 'init', str(repo)], env, home)
    git = ['git', '-C', str(repo)]
    _run([*git, 'fetch', '--depth', '1', step['url'], step['commit']], env, home)
    _run([*git, 'checkout', '--detach', step['commit']], env, home)
    if step.get('recursive'):
        _run([*git, 'submodule', 'update', '--init', '--recursive', '--depth', '1'], env, home)


def execute_step(
    step: dict[str, Any], recipe: Recipe, home: Path, cache: Path, progress_span: tuple[float, float]
) -> None:
    """Ejecuta un paso en el venv y caché del motor, con avance para cada descarga."""
    venv = home / recipe.venv
    python = process.python_de(venv)
    env = process.env_src(
        {
            **os.environ,
            'HF_HOME': str(cache),
            'VIRTUAL_ENV': str(venv),
            'GIT_TERMINAL_PROMPT': '0',
            'CONTENT_STUDIO_PROGRESS_START': str(progress_span[0]),
            'CONTENT_STUDIO_PROGRESS_END': str(progress_span[1]),
        }
    )
    kind = step['kind']
    if kind == 'python':
        _run(['uv', 'python', 'install', step['version']], env, home)
    elif kind == 'venv':
        version = recipe.steps[0]['version']
        venv.parent.mkdir(parents=True, exist_ok=True)
        _run(['uv', 'venv', '--allow-existing', '--python', version, str(venv)], env, home)
    elif kind == 'pip':
        _pip(step, home, python, env)
    elif kind == 'git':
        _git(step, home, env)
    elif kind == 'verify':
        imports = os.pathsep.join(str(home / path) for path in step.get('paths', []))
        if imports:
            env['PYTHONPATH'] = imports + os.pathsep + env['PYTHONPATH']
        _run(
            [str(python), '-c', 'import importlib, sys; importlib.import_module(sys.argv[1])', step['import']],
            env,
            home,
        )
    elif kind == 'hf':
        _run([str(python), '-m', __name__, json.dumps(step)], env, home)


def _file_bytes(folder: Path) -> int:
    total = 0
    for path in folder.rglob('*'):
        try:
            if path.is_file() and not path.is_symlink():
                total += path.stat().st_size
        except FileNotFoundError:  # La descarga puede publicar un parcial con rename.
            continue
    return total


def _download(step: dict) -> None:
    from huggingface_hub import HfApi, snapshot_download

    repo, revision = step['repo'], step['revision']
    allow = step.get('allow_patterns', ['*'])
    ignore = step.get('ignore_patterns', [])
    cache = Path(os.environ['HF_HOME']) / 'hub'
    local = None if step['into'] == 'hf' else Path(step['into']).resolve()
    model_cache = cache / ('models--' + repo.replace('/', '--'))
    info = HfApi().model_info(repo, revision=revision, files_metadata=True)
    total = sum(
        item.size or 0
        for item in info.siblings or []
        if any(fnmatch.fnmatch(item.rfilename, pattern) for pattern in allow)
        and not any(fnmatch.fnmatch(item.rfilename, pattern) for pattern in ignore)
    )
    stop = threading.Event()
    start = float(os.environ.get('CONTENT_STUDIO_PROGRESS_START', '0'))
    end = float(os.environ.get('CONTENT_STUDIO_PROGRESS_END', '1'))

    def report(stage: str, fraction: float) -> None:
        progress.emit(round(start + (end - start) * fraction, 4), stage)

    report(repo, 0.0)

    def monitor() -> None:
        while not stop.wait(1):
            count = _file_bytes(local or model_cache)
            report(f'{count}/{total} bytes', min(count / max(total, 1), 0.99))

    observer = threading.Thread(target=monitor, daemon=True)
    observer.start()
    try:
        snapshot_download(
            repo, revision=revision, cache_dir=cache, local_dir=local, allow_patterns=allow, ignore_patterns=ignore
        )
        if local is None:
            ref = model_cache / 'refs' / 'main'
            ref.parent.mkdir(parents=True, exist_ok=True)
            ref.write_text(revision, encoding='utf-8')
    finally:
        stop.set()
        observer.join()


if __name__ == '__main__':
    _download(json.loads(sys.argv[1]))

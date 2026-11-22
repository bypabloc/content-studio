"""Instalación reanudable con registro de propiedad de los archivos."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from types import TracebackType

from content_studio import paths
from content_studio.common import process, progress
from content_studio.db import jobs, settings
from content_studio.db.connection import utc_now
from content_studio.engines import recipes
from content_studio.engines.recipes import Recipe
from content_studio.engines.steps import _file_bytes, execute_step

EXIT_CODES = {'disk_full': 20, 'engine_external': 21, 'engine_license_required': 22, 'engine_not_installed': 23}


class InstallError(ValueError):
    """Error de un motor con código para el CLI o la API."""

    def __init__(self, code: str) -> None:
        """Conserva el código de error para localizarlo."""
        super().__init__(code)
        self.code = code


def _ignore_missing_rmtree_error(
    _: Callable[..., object],
    __: str,
    exc_info: tuple[type[BaseException], BaseException, TracebackType | None],
) -> None:
    error = exc_info[1]
    if not isinstance(error, FileNotFoundError):
        raise error


def _rmtree_missing_ok(path: Path) -> None:
    """Borra una ruta propia y tolera solo entradas que desaparecen durante el recorrido."""
    target: Path | str = path
    if os.name == 'nt':
        absolute = str(path.resolve())
        target = '\\\\?\\UNC\\' + absolute[2:] if absolute.startswith('\\\\') else '\\\\?\\' + absolute
    shutil.rmtree(target, onerror=_ignore_missing_rmtree_error)


def read_manifest(home: Path) -> dict:
    """Lee el registro de instalación si está completo."""
    try:
        result = json.loads((home / 'install.json').read_text(encoding='utf-8'))
    except (FileNotFoundError, ValueError):
        return {}
    return result if isinstance(result, dict) else {}


def _write_json(path: Path, data: dict) -> None:
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data), encoding='utf-8')
    temporary.replace(path)


def _owned_paths(root: Path, engine: str) -> tuple[Path, Path]:
    home, cache = root / engine, root / 'hf' / engine
    if home.resolve() != home or cache.resolve() != cache:
        raise InstallError('engine_external')
    return home, cache


def engine_venv(recipe: Recipe, root: Path) -> Path:
    """Venv administrado de un motor, con respaldo al externo en desarrollo."""
    return paths.engine_root(recipe.family, recipe.venv, recipe.engine, root) / recipe.venv


def remove_paths(root: Path, engine: str, manifest: dict) -> None:
    """Borra únicamente las dos rutas que puede reclamar el motor indicado."""
    allowed = _owned_paths(root, engine)
    owned = manifest.get('paths', [])
    if not isinstance(owned, list):
        raise InstallError('engine_external')
    locations = {path.relative_to(root).as_posix(): path for path in allowed}
    if not all(isinstance(item, str) and item in locations for item in owned):
        raise InstallError('engine_external')
    for path in reversed(allowed):
        if path.relative_to(root).as_posix() in owned and path.exists():
            _rmtree_missing_ok(path)
    cache_parent = root / 'hf'
    if cache_parent.is_dir() and not any(cache_parent.iterdir()):
        cache_parent.rmdir()


def uninstall(engine: str, root: Path, force: bool = False) -> None:
    """Desinstala una instalación propia o, con confirmación, solo el venv externo conocido."""
    recipe = recipes.load(engine)
    root = root.resolve()
    home, _ = _owned_paths(root, engine)
    manifest = read_manifest(home)
    if manifest.get('owner') != 'app':
        venv = engine_venv(recipe, root)
        if not venv.is_dir():
            raise InstallError('engine_not_installed')
        if not force:
            raise InstallError('engine_external')
        target = venv.resolve()
        external_root = paths.NARRATION if recipe.family == 'narration' else paths.MUSIC
        try:
            relative = target.relative_to(external_root.resolve()).as_posix()
        except ValueError:
            raise InstallError('engine_external') from None
        if venv.is_symlink() or relative != recipe.venv:
            raise InstallError('engine_external')
        _rmtree_missing_ok(target)
        return
    remove_paths(root, engine, manifest)


def install(recipe: Recipe, root: Path, repair: bool = False) -> dict:
    """Instala el motor y registra qué rutas pertenecen a la app."""
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    home, cache = _owned_paths(root, recipe.engine)
    current = read_manifest(home)
    pending = home / 'installing.json'
    own = current.get('owner') == 'app'
    if repair and not own:
        raise InstallError('engine_external')
    if not repair and own and current.get('recipe_version') == recipe.version and not pending.exists():
        return current
    if (home.exists() or cache.exists()) and not own and not pending.is_file():
        raise InstallError('engine_external')
    existing = _file_bytes(home) + _file_bytes(cache)
    if shutil.disk_usage(root).free + existing < recipe.size_gb * 1.2 * 10**9:
        raise InstallError('disk_full')
    home.mkdir(exist_ok=True)
    _write_json(pending, {'owner': 'app', 'recipe_version': recipe.version})
    markers = home / 'steps'
    markers.mkdir(exist_ok=True)
    family = home / recipe.family
    family.mkdir(exist_ok=True)
    if repair:
        venv = family / recipe.venv
        if venv.exists():
            if not venv.resolve().is_relative_to(family) or venv.resolve() != venv:
                raise InstallError('engine_external')
            _rmtree_missing_ok(venv)
        for index, step in enumerate(recipe.steps):
            if step['kind'] in ('python', 'venv', 'pip', 'verify'):
                (markers / f'{recipe.version}-{index}.done').unlink(missing_ok=True)
    for index, step in enumerate(recipe.steps):
        done = markers / f'{recipe.version}-{index}.done'
        if not done.is_file():
            start = index / len(recipe.steps)
            end = (index + 1) / len(recipe.steps)
            progress.emit(start, step['kind'])
            execute_step(step, recipe, family, cache, (start, end))
            done.touch()
    result = {
        'owner': 'app',
        'recipe_version': recipe.version,
        'installed_at': utc_now(),
        'paths': [path.relative_to(root).as_posix() for path in (home, cache)],
        'size_bytes': _file_bytes(home) + _file_bytes(cache),
    }
    _write_json(home / 'install.json', result)
    pending.unlink()
    progress.emit(1, 'installed')
    return result


def managed_ready(recipe: Recipe, root: Path) -> bool:
    """Comprueba el intérprete y confirma que no hay una instalación en curso."""
    base = root / recipe.engine
    return not (base / 'installing.json').exists() and process.python_de(base / recipe.family / recipe.venv).is_file()


def commercial(engine: str) -> bool:
    """Las licencias no comerciales declaradas en el registro requieren aceptación."""
    from content_studio.narration.engines.registry import ENGINES

    return engine not in ENGINES or ENGINES[engine].commercial


def check_license(conn: sqlite3.Connection, engine: str) -> None:
    """Hace cumplir la aceptación también para los trabajos encolados desde el CLI."""
    if not commercial(engine) and settings.get(conn, f'license.accepted.{engine}') is not True:
        raise InstallError('engine_license_required')


@lru_cache(maxsize=32)
def _external_size(venv: Path, modified: int) -> int:
    return _file_bytes(venv)


def list_engines(conn: sqlite3.Connection, root: Path) -> list[dict]:
    """Combina las recetas, el estado en disco y los trabajos activos de instalación."""
    active = {
        job['params'].get('engine'): job['id']
        for job in jobs.list_jobs(conn, kind='engine.install')
        if job['status'] in ('queued', 'running')
    }
    entries = []
    for recipe in recipes.load_all():
        home = root / recipe.engine
        manifest = read_manifest(home)
        verification = settings.get(conn, f'engine.verify.{recipe.engine}')
        venv = engine_venv(recipe, root)
        size = manifest.get('size_bytes', 0)
        owner = None
        if recipe.engine in active:
            state = 'installing'
        elif manifest.get('owner') == 'app' or (home / 'installing.json').exists():
            owner = 'app'
            failed = isinstance(verification, dict) and not verification.get('ok')
            state = 'installed' if managed_ready(recipe, root) and not failed else 'broken'
        elif venv.is_dir() and not venv.is_relative_to(root):
            owner, state = 'external', 'external'
            size = _external_size(venv, venv.stat().st_mtime_ns)
        else:
            state = 'missing'
        entries.append(
            {
                'engine': recipe.engine,
                'family': recipe.family,
                'size_gb': recipe.size_gb,
                'vram_gb': recipe.vram_gb,
                'cpu': recipe.cpu,
                'license': recipe.license,
                'commercial': commercial(recipe.engine),
                'status': state,
                'owner': owner,
                'size_bytes': size,
                'job_id': active.get(recipe.engine),
                'verification': verification,
            }
        )
    return entries

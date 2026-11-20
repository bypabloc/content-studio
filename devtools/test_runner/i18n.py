"""Etapa `i18n` del test-runner: catálogos parejos (spec 007, D-8).

Revisa messages/{es,en,pt}.json: JSON válido, sin claves repetidas, las mismas claves y los mismos {parámetros} en
cada idioma, orden alfabético y sin valores vacíos. Las claves en uso y los textos sueltos llegan en los ciclos 3 y 7.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .. import paths

CATALOG_DIR = paths.ROOT / 'server' / 'src' / 'content_studio' / 'messages'
LOCALES = ('es', 'en', 'pt')
PLACEHOLDER = re.compile(r'\{(\w+)\}')


def _show(path: Path) -> str:
    """Ruta relativa a la raíz del repo cuando se puede, para que el aviso sea corto."""
    try:
        return path.relative_to(paths.ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _load(path: Path, problems: list[str]) -> dict[str, str] | None:
    """Carga el catálogo con sus claves en orden; cada clave repetida es un problema, y un JSON inválido corta."""
    repeated: list[str] = []

    def keep_last(pairs: list[tuple[str, str]]) -> dict[str, str]:
        seen: dict[str, str] = {}
        for key, text in pairs:
            if key in seen:
                repeated.append(key)
            seen[key] = text
        return seen

    try:
        data = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=keep_last)
    except (OSError, json.JSONDecodeError) as error:
        problems.append(f'{_show(path)}: not valid JSON or unreadable ({error})')
        return None
    problems.extend(f'{_show(path)}: key "{key}" appears twice' for key in repeated)
    return data


def check_catalogs(directory: Path = CATALOG_DIR) -> list[str]:
    """Una línea por problema, con archivo y clave. Vacío si los catálogos están parejos."""
    problems: list[str] = []
    catalogs: dict[str, dict[str, str]] = {}
    for locale in LOCALES:
        path = directory / f'{locale}.json'
        data = _load(path, problems)
        if data is None:
            continue
        catalogs[locale] = data
        keys = list(data)
        if keys != sorted(keys):
            problems.append(f'{_show(path)}: keys are not in alphabetical order')
        for key, text in data.items():
            if not isinstance(text, str) or not text.strip() or text != text.strip():
                problems.append(f'{_show(path)}: key "{key}" has an empty value or spaces at its edges')
    if len(catalogs) < len(LOCALES):
        return problems

    every_key = set().union(*(set(data) for data in catalogs.values()))
    for locale, data in catalogs.items():
        for key in sorted(every_key - set(data)):
            problems.append(f'{_show(directory / f"{locale}.json")}: key "{key}" is missing')

    base = catalogs['es']
    for locale in LOCALES[1:]:
        for key in sorted(set(base) & set(catalogs[locale])):
            if set(PLACEHOLDER.findall(base[key])) != set(PLACEHOLDER.findall(catalogs[locale][key])):
                problems.append(
                    f'{_show(directory / f"{locale}.json")}: key "{key}" has other {{parameters}} than es.json'
                )
    return problems


def run(files: list[Path], catalog_dir: Path = CATALOG_DIR) -> dict:
    """Etapa `i18n`: falla con cada problema de los catálogos. `files` no cambia el resultado: revisa todo."""
    problems = check_catalogs(catalog_dir)
    return {'stage': 'i18n', 'status': 'fail' if problems else 'pass', 'detail': '\n'.join(problems)}

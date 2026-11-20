"""Etapa `i18n` del test-runner: catálogos parejos (spec 007, D-8).

Revisa messages/{es,en,pt}.json: JSON válido, sin claves repetidas, las mismas claves y los mismos {parámetros} en
cada idioma, orden alfabético y sin valores vacíos. Las claves en uso y los textos sueltos llegan en los ciclos 3 y 7.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from .. import paths
from .i18n_loose import check_loose

CATALOG_DIR = paths.ROOT / 'server' / 'src' / 'content_studio' / 'messages'
CONFIG = paths.ROOT / 'tests' / 'validators' / 'i18n.json'
LOCALES = ('es', 'en', 'pt')
PLACEHOLDER = re.compile(r'\{(\w+)\}')
T_CALL = re.compile(r"""\bt\(\s*['"]([\w.]+)['"]""")


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


def client_keys(src: Path) -> dict[str, list[str]]:
    """Clave literal de `t('…')` en client/src → sus lugares `archivo:línea`. Las claves dinámicas no se ven aquí."""
    found: dict[str, list[str]] = {}
    for file in sorted(src.rglob('*')):
        if file.suffix not in {'.ts', '.tsx'}:
            continue
        lines = file.read_text(encoding='utf-8').splitlines()
        for number, line in enumerate(lines, start=1):
            for match in T_CALL.finditer(line):
                found.setdefault(match.group(1), []).append(f'{_show(file)}:{number}')
    return found


def _name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _text(node: ast.expr) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _code_of(node: ast.Call | ast.Dict) -> str | None:
    """Código de error: `ApiError(status, 'code', …)` o `{'code': 'code', …}` (la forma de `validate`)."""
    if isinstance(node, ast.Call):
        if _name(node.func) != 'ApiError' or len(node.args) < 2:
            return None
        return _text(node.args[1])
    for key, value in zip(node.keys, node.values, strict=False):
        if isinstance(key, ast.Constant) and key.value == 'code':
            return _text(value)
    return None


def server_keys(src: Path) -> dict[str, list[str]]:
    """Clave de `t('…')` en el server (messages.t y similares) → sus lugares `archivo:línea`, con ast."""
    found: dict[str, list[str]] = {}
    for file in sorted(src.rglob('*.py')):
        for node in ast.walk(ast.parse(file.read_text(encoding='utf-8'))):
            if isinstance(node, ast.Call) and _name(node.func) == 't' and node.args:
                key = _text(node.args[0])
                if key is not None:
                    found.setdefault(key, []).append(f'{_show(file)}:{node.lineno}')
    return found


def server_codes(src: Path) -> dict[str, list[str]]:
    """Código de error del server → sus lugares `archivo:línea` (con ast, sin ejecutar nada)."""
    found: dict[str, list[str]] = {}
    for file in sorted(src.rglob('*.py')):
        for node in ast.walk(ast.parse(file.read_text(encoding='utf-8'))):
            if not isinstance(node, (ast.Call, ast.Dict)):
                continue
            code = _code_of(node)
            if code is not None:
                found.setdefault(code, []).append(f'{_show(file)}:{node.lineno}')
    return found


def check_usage(
    root: Path = paths.ROOT, catalog: dict[str, str] | None = None, config: dict | None = None
) -> list[str]:
    """Cada `t('…')` del client y cada código de error del server tiene su clave; ninguna clave sobra.

    Una clave sobra si nadie la usa y no entra en un prefijo dinámico declarado (`dynamicPrefixes`); cada prefijo
    declarado debe tener al menos una clave.
    """
    if catalog is None:
        catalog = _load_dict(CATALOG_DIR / 'es.json')
    if config is None:
        config = load_config(CONFIG)
    prefixes = config.get('dynamicPrefixes', [])
    used_by_client = client_keys(root / 'client' / 'src')
    used_by_server = server_keys(root / 'server' / 'src' / 'content_studio')
    codes = server_codes(root / 'server' / 'src' / 'content_studio')
    problems: list[str] = []
    for key, places in sorted({**used_by_server, **used_by_client}.items()):
        if key not in catalog:
            problems.append(f'{places[0]}: t("{key}") has no text in messages/es.json')
    for code, places in sorted(codes.items()):
        if f'error.{code}' not in catalog:
            problems.append(f'{places[0]}: error code "{code}" has no text "error.{code}" in messages/es.json')
    used = set(used_by_client) | set(used_by_server) | {f'error.{code}' for code in codes}
    for key in sorted(catalog):
        if key not in used and not any(key.startswith(prefix) for prefix in prefixes):
            problems.append(f'messages/es.json: key "{key}" is not used')
    for prefix in prefixes:
        if not any(key.startswith(prefix) for key in catalog):
            problems.append(f'tests/validators/i18n.json: dynamic prefix "{prefix}" has no keys')
    return problems


def _load_dict(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding='utf-8'))


def load_config(path: Path = CONFIG) -> dict:
    """Configuración de la etapa (tests/validators/i18n.json): prefijos dinámicos y lo que sumen los ciclos 7 y 9."""
    return json.loads(path.read_text(encoding='utf-8'))


def run(files: list[Path], catalog_dir: Path = CATALOG_DIR, root: Path = paths.ROOT) -> dict:
    """Etapa `i18n`: catálogos parejos, claves en uso y textos sueltos. `files` no cambia el resultado: revisa todo."""
    problems = check_catalogs(catalog_dir)
    if not problems:
        catalog = _load_dict(catalog_dir / 'es.json')
        config = load_config(root / 'tests' / 'validators' / 'i18n.json')
        problems = check_usage(root, catalog, config)
    if not problems:
        try:
            problems = [finding.message() for finding in check_loose(root)]
        except RuntimeError as error:
            problems = [str(error)]
    return {'stage': 'i18n', 'status': 'fail' if problems else 'pass', 'detail': '\n'.join(problems)}

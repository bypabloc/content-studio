"""`python -m devtools version` (spec 022, D-7, AC-4): la misma versión en todos los manifiestos."""

from __future__ import annotations

import json

from devtools import version

FILES = {
    'client/src-tauri/tauri.conf.json': '{\n  "productName": "Content Studio",\n  "version": "0.1.0",\n  "x": 1\n}\n',
    'client/package.json': '{\n  "name": "client",\n  "version": "0.1.0",\n  "dependencies": {}\n}\n',
    'package.json': '{\n  "name": "content-studio",\n  "version": "0.1.0"\n}\n',
    'client/src-tauri/Cargo.toml': (
        '[package]\nname = "content-studio"\nversion = "0.1.0"\n\n[dependencies]\nserde = { version = "=1" }\n'
    ),
    'server/pyproject.toml': '[project]\r\nname = "content-studio"\r\nversion = "0.1.0"\r\n\r\n[tool.uv]\r\n',
    'client/src-tauri/Cargo.lock': (
        '[[package]]\nname = "serde"\nversion = "1.0.0"\n\n[[package]]\nname = "content-studio"\nversion = "0.1.0"\n'
    ),
    'uv.lock': '[[package]]\nname = "content-studio"\nversion = "0.1.0"\nsource = { editable = "server" }\n',
}


def _repo(tmp_path):
    for rel, text in FILES.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_bytes(text.encode('utf-8'))
    return tmp_path


def test_ac4_set_writes_the_version_in_every_manifest_and_check_passes(tmp_path, capsys):
    """`version 1.2.3` cambia solo la versión de la app en cada archivo; `--check` sale con 0."""
    root = _repo(tmp_path)

    assert version.main(['1.2.3'], root) == 0
    assert set(version.read(root).values()) == {'1.2.3'}
    assert version.main(['--check'], root) == 0
    assert json.loads(capsys.readouterr().out.splitlines()[-1]) == {'version': '1.2.3'}
    assert 'serde = { version = "=1" }' in (root / 'client/src-tauri/Cargo.toml').read_text(encoding='utf-8')
    assert 'name = "serde"\nversion = "1.0.0"' in (root / 'client/src-tauri/Cargo.lock').read_text(encoding='utf-8')
    assert b'\r\n' in (root / 'server/pyproject.toml').read_bytes()


def test_ac4_check_names_the_file_that_differs(tmp_path, capsys):
    """Con un manifiesto distinto, `--check` sale con 1 y nombra el archivo y su versión."""
    root = _repo(tmp_path)
    version.main(['1.2.3'], root)
    pkg = root / 'client/package.json'
    pkg.write_text(pkg.read_text(encoding='utf-8').replace('1.2.3', '1.2.4'), encoding='utf-8')

    assert version.main(['--check'], root) == 1
    assert 'client/package.json: 1.2.4 (expected 1.2.3)' in capsys.readouterr().err


def test_ac4_expect_compares_with_the_tag(tmp_path, capsys):
    """`--check --expect` (el tag de la release) falla si la versión no es la del tag."""
    root = _repo(tmp_path)

    assert version.main(['--check', '--expect', '0.1.0'], root) == 0
    assert version.main(['--check', '--expect', '0.2.0'], root) == 1
    assert 'expected 0.2.0' in capsys.readouterr().err


def test_ac4_an_invalid_version_exits_2(tmp_path, capsys):
    """`version 1.2` no es semver: exit 2 y no toca nada."""
    root = _repo(tmp_path)

    assert version.main(['1.2'], root) == 2
    assert set(version.read(root).values()) == {'0.1.0'}
    assert 'x.y.z' in capsys.readouterr().err


def test_problems_is_empty_outside_the_repo(tmp_path):
    """La etapa validators llama a `problems`; sin los manifiestos (una raíz de prueba) no hay nada que comparar."""
    assert version.problems(tmp_path) == []
    assert version.problems(_repo(tmp_path)) == []


def test_without_a_version_or_check_it_shows_the_usage(tmp_path, capsys):
    """Sin argumentos no hay nada que hacer: exit 2 con el uso."""
    assert version.main([], _repo(tmp_path)) == 2
    assert 'usage' in capsys.readouterr().err

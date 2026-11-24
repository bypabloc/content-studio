"""devtools worktree: prepare, close y los enlaces a los venvs del principal."""

from __future__ import annotations

import shutil
import subprocess

from devtools import worktree
from devtools.paths import ROOT

GIT = ['git', '-c', 'user.name=t', '-c', 'user.email=t@t']


def test_missing_and_links_not_touch_the_destination(tmp_path):
    main, wt = tmp_path / 'main', tmp_path / 'wt'
    (main / 'server/data/narration/.venv-qwen/bin').mkdir(parents=True)
    (main / 'server/data/narration/.venv-qwen/bin/python').write_text('x')
    (main / 'server/data/music/models/ace').mkdir(parents=True)
    (main / 'server/data/narration/reference').mkdir(parents=True)
    (main / 'server/data/narration/reference/clara.wav').write_bytes(b'RIFF')
    (main / 'server/data/narration/voices/yesid').mkdir(parents=True)
    (wt / 'server/data/narration/reference').mkdir(parents=True)
    folders, audios = worktree.missing(main, wt)
    names = sorted(p.as_posix() for p in folders)
    assert names == [
        'server/data/music/models',
        'server/data/narration/.venv-qwen',
        'server/data/narration/voices/yesid',
    ]
    assert [a.as_posix() for a in audios] == ['server/data/narration/reference/clara.wav']
    for rel in folders:
        worktree.link(main / rel, wt / rel)
    assert (wt / 'server/data/narration/.venv-qwen/bin/python').read_text() == 'x'
    assert worktree.missing(main, wt)[0] == []
    assert worktree.remove_links(wt) == 3
    assert (main / 'server/data/narration/.venv-qwen/bin/python').is_file()  # el principal queda intacto
    assert not (wt / 'server/data/narration/.venv-qwen').exists()


def test_prepare_and_close_in_a_repo_real(tmp_path, monkeypatch):
    main = tmp_path / 'repo'
    remote = tmp_path / 'remote.git'
    subprocess.run(['git', 'init', '-q', '--bare', '-b', 'dev', str(remote)], check=True)
    subprocess.run(['git', 'clone', '-q', str(remote), str(main)], check=True, capture_output=True)
    shutil.copy(ROOT / '.gitignore', main / '.gitignore')  # el real: en POSIX sus enlaces son symlinks, no carpetas
    (main / 'server/data/music/models/ace').mkdir(parents=True)
    subprocess.run([*GIT, 'add', '.'], cwd=main, check=True)
    subprocess.run([*GIT, 'commit', '-qm', 'base'], cwd=main, check=True)
    subprocess.run(['git', 'push', '-q', 'origin', 'HEAD:dev'], cwd=main, check=True, capture_output=True)
    wt = tmp_path / 'repo-worktrees' / 'tema'
    subprocess.run(['git', 'worktree', 'add', '-q', str(wt), '-b', 'feature/tema'], cwd=main, check=True)
    monkeypatch.chdir(main)
    assert worktree.prepare(main.resolve(), 'tema') == 0
    assert (wt / 'server/data/music/models/ace').is_dir() and (wt / 'tmp').is_dir()
    subprocess.run(['git', 'fetch', '-q', 'origin'], cwd=main, check=True)
    assert worktree.close(main.resolve(), 'tema') == 0
    assert not wt.exists() and (main / 'server/data/music/models/ace').is_dir()
    assert worktree.close(main.resolve(), 'tema') == 2


def test_node_modules_is_not_linked_because_bun_install_would_write_to_main(tmp_path):
    """client/ y tests/e2e son workspaces de bun: `bun install` en el worktree crea su propio node_modules."""
    main, wt = tmp_path / 'main', tmp_path / 'wt'
    (main / 'node_modules/@cspell').mkdir(parents=True)
    wt.mkdir()
    assert worktree.missing(main, wt)[0] == []


def test_prepare_installs_with_bun_and_shares_the_cargo_target(tmp_path, monkeypatch):
    """D-10: `prepare` corre `bun install` en el worktree y enlaza su target de Cargo a <principal>/tmp/cargo-target."""
    main = tmp_path / 'repo'
    remote = tmp_path / 'remote.git'
    subprocess.run(['git', 'init', '-q', '--bare', '-b', 'dev', str(remote)], check=True)
    subprocess.run(['git', 'clone', '-q', str(remote), str(main)], check=True, capture_output=True)
    shutil.copy(ROOT / '.gitignore', main / '.gitignore')
    (main / 'package.json').write_text('{}')
    (main / 'client/src-tauri').mkdir(parents=True)
    (main / 'client/src-tauri/Cargo.toml').write_text('')
    subprocess.run([*GIT, 'add', '.'], cwd=main, check=True)
    subprocess.run([*GIT, 'commit', '-qm', 'base'], cwd=main, check=True)
    subprocess.run(['git', 'push', '-q', 'origin', 'HEAD:dev'], cwd=main, check=True, capture_output=True)
    wt = tmp_path / 'repo-worktrees' / 'tema'
    subprocess.run(['git', 'worktree', 'add', '-q', str(wt), '-b', 'feature/tema'], cwd=main, check=True)
    installed = []
    monkeypatch.setattr(worktree, '_bun_install', lambda root: installed.append(root) or 0)
    monkeypatch.chdir(main)
    assert worktree.prepare(main.resolve(), 'tema') == 0
    assert installed == [wt]
    assert worktree.is_link(wt / 'client/src-tauri/target') and (main / 'tmp/cargo-target').is_dir()
    subprocess.run(['git', 'fetch', '-q', 'origin'], cwd=main, check=True)
    assert worktree.close(main.resolve(), 'tema') == 0
    assert (main / 'tmp/cargo-target').is_dir() and not wt.exists()


def test_prepare_keeps_an_existing_cargo_target(tmp_path, monkeypatch):
    main, wt = tmp_path / 'main', tmp_path / 'wt'
    (main / 'client/src-tauri').mkdir(parents=True)
    (wt / 'client/src-tauri/target/debug').mkdir(parents=True)
    assert worktree._cargo_target(main, wt) is False
    assert not worktree.is_link(wt / 'client/src-tauri/target') and (wt / 'client/src-tauri/target/debug').is_dir()


def test_bun_install_returns_127_when_bun_is_not_installed(tmp_path, monkeypatch):
    def no_bun(*args, **kwargs):
        raise FileNotFoundError('bun')

    monkeypatch.setattr(worktree.subprocess, 'run', no_bun)
    assert worktree._bun_install(tmp_path) == 127


def test_bun_install_uses_the_hoisted_linker_so_paths_fit_windows_limits(tmp_path, monkeypatch):
    """Con el enlazador anidado, Windows sin rutas largas falla al copiar paquetes profundos: usa hoisted."""
    calls = []

    def fake(command, **kwargs):
        calls.append((command, kwargs['cwd']))
        return type('Done', (), {'returncode': 0})()

    monkeypatch.setattr(worktree.subprocess, 'run', fake)
    assert worktree._bun_install(tmp_path) == 0
    assert calls == [(['bun', 'install', '--frozen-lockfile', '--linker', 'hoisted'], tmp_path)]


def test_prepare_stops_and_says_so_when_bun_install_fails(tmp_path, monkeypatch, capsys):
    main, wt = tmp_path / 'main', tmp_path / 'wt'
    main.mkdir()
    wt.mkdir()
    (wt / 'package.json').write_text('{}')
    monkeypatch.setattr(worktree, 'search', lambda main_root, name: {'root': str(wt), 'head': '', 'branch': ''})
    monkeypatch.setattr(worktree, '_bun_install', lambda root: 1)
    assert worktree.prepare(main, 'tema') == 1
    assert 'bun install failed' in capsys.readouterr().err


def test_close_finishes_when_windows_cannot_delete_the_held_folder(tmp_path, monkeypatch):
    """Regresión: en Windows, `git worktree remove` vacía y desregistra el worktree pero falla al borrar la carpeta
    que otro proceso tiene como cwd («Permission denied»); `close` cortaba ahí y dejaba las ramas."""
    main = tmp_path / 'repo'
    remote = tmp_path / 'remote.git'
    subprocess.run(['git', 'init', '-q', '--bare', '-b', 'dev', str(remote)], check=True)
    subprocess.run(['git', 'clone', '-q', str(remote), str(main)], check=True, capture_output=True)
    (main / 'a.txt').write_text('a')
    subprocess.run([*GIT, 'add', '.'], cwd=main, check=True)
    subprocess.run([*GIT, 'commit', '-qm', 'base'], cwd=main, check=True)
    subprocess.run(['git', 'push', '-q', 'origin', 'HEAD:dev'], cwd=main, check=True, capture_output=True)
    wt = tmp_path / 'repo-worktrees' / 'tema'
    subprocess.run(['git', 'worktree', 'add', '-q', str(wt), '-b', 'fix/tema'], cwd=main, check=True)
    subprocess.run(['git', 'fetch', '-q', 'origin'], cwd=main, check=True)
    real = worktree._git

    def git_held(cwd, *args):
        r = real(cwd, *args)
        if args[:2] == ('worktree', 'remove'):
            wt.mkdir(parents=True, exist_ok=True)  # la carpeta vacía que Windows no deja borrar
            return subprocess.CompletedProcess(r.args, 1, '', "error: failed to delete '...': Permission denied")
        return r

    monkeypatch.setattr(worktree, '_git', git_held)
    monkeypatch.chdir(main)
    assert worktree.close(main.resolve(), 'tema') == 0
    assert 'fix/tema' not in real(main, 'branch', '--list', 'fix/tema').stdout
    assert worktree.search(main.resolve(), 'tema') is None


def test_is_link_recognizes_junctions(tmp_path):
    (tmp_path / 'destino').mkdir()
    worktree.link(tmp_path / 'destino', tmp_path / 'enlace')
    assert worktree.is_link(tmp_path / 'enlace') and not worktree.is_link(tmp_path / 'destino')


def test_remove_links_takes_an_old_node_modules_link_and_keeps_its_target(tmp_path):
    """Un worktree de antes del cambio tiene node_modules enlazado al principal: `close` lo quita sin borrarlo."""
    principal = tmp_path / 'principal-node-modules'
    principal.mkdir()
    (principal / 'keep.txt').write_text('x', encoding='utf-8')
    root = tmp_path / 'worktree'
    root.mkdir()
    worktree.link(principal, root / 'node_modules')

    assert worktree.remove_links(root) == 1
    assert not (root / 'node_modules').exists()
    assert (principal / 'keep.txt').is_file()


def test_prepare_drops_an_old_node_modules_link_before_bun_install(tmp_path, monkeypatch):
    """bun install escribiría en el principal por el enlace heredado: `prepare` lo quita antes de instalar."""
    main = tmp_path / 'repo'
    remote = tmp_path / 'remote.git'
    subprocess.run(['git', 'init', '-q', '--bare', '-b', 'dev', str(remote)], check=True)
    subprocess.run(['git', 'clone', '-q', str(remote), str(main)], check=True, capture_output=True)
    (main / '.gitignore').write_text('node_modules/\ntmp/\n')
    (main / 'package.json').write_text('{}')
    subprocess.run([*GIT, 'add', '.'], cwd=main, check=True)
    subprocess.run([*GIT, 'commit', '-qm', 'base'], cwd=main, check=True)
    subprocess.run(['git', 'push', '-q', 'origin', 'HEAD:dev'], cwd=main, check=True, capture_output=True)
    wt = tmp_path / 'repo-worktrees' / 'tema'
    subprocess.run(['git', 'worktree', 'add', '-q', str(wt), '-b', 'feature/tema'], cwd=main, check=True)
    (main / 'node_modules').mkdir()
    (main / 'node_modules' / 'keep.txt').write_text('x', encoding='utf-8')
    worktree.link(main / 'node_modules', wt / 'node_modules')
    seen = []
    monkeypatch.setattr(worktree, '_bun_install', lambda root: seen.append((root / 'node_modules').exists()) or 0)
    monkeypatch.chdir(main)

    assert worktree.prepare(main.resolve(), 'tema') == 0
    assert seen == [False]
    assert (main / 'node_modules' / 'keep.txt').is_file()


def test_repo_gitignore_hides_every_link_prepare_creates(tmp_path):
    """En POSIX cada enlace de `prepare` es un symlink, que git no trata como carpeta: el .gitignore del repo tiene que
    cubrirlo sin `/` final, o `close` ve el árbol sucio (fallo de CI de la 011)."""
    repo = tmp_path / 'repo'
    repo.mkdir()
    subprocess.run(['git', 'init', '-q', str(repo)], check=True)
    shutil.copy(ROOT / '.gitignore', repo / '.gitignore')
    subprocess.run([*GIT, 'add', '.gitignore'], cwd=repo, check=True)
    subprocess.run([*GIT, 'commit', '-qm', 'base'], cwd=repo, check=True)
    for rel in worktree.LINKS:
        link_path = repo / rel.replace('*', '-x')
        link_path.parent.mkdir(parents=True, exist_ok=True)
        target = tmp_path / 'principal' / link_path.name
        target.mkdir(parents=True, exist_ok=True)
        worktree.link(target, link_path)
    status = subprocess.run(['git', 'status', '--porcelain'], cwd=repo, capture_output=True, text=True, check=True)
    assert status.stdout == ''

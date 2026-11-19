"""devtools worktree: prepare, close y los enlaces a los venvs del principal."""

from __future__ import annotations

import subprocess

from devtools import worktree

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
    # Sin `/` final, como el .gitignore del repo: en POSIX el enlace es un symlink, no una carpeta para git.
    (main / '.gitignore').write_text('models\ntmp/\n')
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


def test_missing_links_node_modules_so_spelling_works_in_a_worktree(tmp_path):
    main, wt = tmp_path / 'main', tmp_path / 'wt'
    (main / 'node_modules/@cspell').mkdir(parents=True)
    wt.mkdir()
    assert [p.as_posix() for p in worktree.missing(main, wt)[0]] == ['node_modules']


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

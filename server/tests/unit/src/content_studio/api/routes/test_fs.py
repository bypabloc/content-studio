"""Explorador del editor (spec 017, D-10, AC-3): solo lee carpetas y medios; oculta los ocultos; no escribe."""

from __future__ import annotations

from pathlib import Path


def test_roots_offer_the_home_folder(api):
    """Las raíces del explorador incluyen la carpeta de usuario."""
    roots = api.client.get('/fs/roots', headers=api.headers).json()['roots']

    assert {'name': 'home', 'path': str(Path.home())} in roots


def test_list_shows_folders_and_the_media_kinds_asked_for_and_hides_dotfiles(api):
    """Con `kinds=audio`, se ven las carpetas y los audios; los archivos de otro tipo y los ocultos no salen."""
    folder = api.tmp / 'carpeta'
    (folder / 'sub').mkdir(parents=True)
    (folder / 'a.wav').write_bytes(b'')
    (folder / 'b.txt').write_bytes(b'')
    (folder / '.oculto.wav').write_bytes(b'')

    response = api.client.get('/fs/list', params={'path': str(folder), 'kinds': 'audio'}, headers=api.headers)

    assert sorted(entry['name'] for entry in response.json()['entries']) == ['a.wav', 'sub']


def test_a_folder_that_does_not_exist_is_404(api):
    """Una carpeta que no existe responde 404 con su código del catálogo."""
    response = api.client.get(
        '/fs/list', params={'path': str(api.tmp / 'no-existe'), 'kinds': 'audio'}, headers=api.headers
    )

    assert response.status_code == 404
    assert response.json()['code'] == 'fs_path_not_found'

"""Explorador del editor (spec 017, D-10, AC-3): solo lee carpetas y medios; oculta los ocultos; no escribe."""

from __future__ import annotations

from pathlib import Path

from content_studio.common import ffmpeg


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


def test_list_supports_images_and_mixed_media(api):
    """AC-3: el explorador lista imágenes y puede combinar audio, video e imagen."""
    folder = api.tmp / 'media'
    folder.mkdir()
    (folder / 'a.wav').write_bytes(b'audio')
    (folder / 'b.mp4').write_bytes(b'video')
    (folder / 'c.png').write_bytes(b'image')
    (folder / 'd.txt').write_bytes(b'text')

    images = api.client.get('/fs/list', params={'path': str(folder), 'kinds': 'image'}, headers=api.headers)
    mixed = api.client.get('/fs/list', params={'path': str(folder), 'kinds': 'audio,video,image'}, headers=api.headers)

    assert [entry['name'] for entry in images.json()['entries']] == ['c.png']
    assert [entry['name'] for entry in mixed.json()['entries']] == ['a.wav', 'b.mp4', 'c.png']


def test_roots_include_existing_explorer_favorites(api):
    """Las carpetas favoritas del explorador salen junto a las raíces del sistema."""
    favorite = api.tmp / 'favorite'
    favorite.mkdir()
    api.client.put('/settings/editor.favorites', json={'value': [str(favorite)]}, headers=api.headers)

    roots = api.client.get('/fs/roots', headers=api.headers).json()['roots']

    assert {'name': 'favorite', 'path': str(favorite)} in roots


def test_roots_ignore_favorites_when_the_saved_setting_is_not_a_list(api):
    """Un valor guardado corrupto no debe romper el explorador de carpetas."""
    api.client.put('/settings/editor.favorites', json={'value': None}, headers=api.headers)

    response = api.client.get('/fs/roots', headers=api.headers)

    assert response.status_code == 200


def test_audio_preview_streams_only_audio_files(api):
    """El reproductor del explorador puede leer audio por GET sin agregar escrituras a /fs."""
    source = api.tmp / 'preview.wav'
    source.write_bytes(b'audio bytes')

    response = api.client.get('/fs/media', params={'path': str(source)}, headers=api.headers)

    assert response.status_code == 200
    assert response.content == b'audio bytes'
    assert response.headers['content-type'].startswith('audio/')


def test_audio_preview_rejects_non_audio_and_missing_files(api):
    """La vista previa no sirve archivos que no existan o no sean audio."""
    image = api.tmp / 'cover.png'
    image.write_bytes(b'image')

    unsupported = api.client.get('/fs/media', params={'path': str(image)}, headers=api.headers)
    missing = api.client.get('/fs/media', params={'path': str(api.tmp / 'gone.wav')}, headers=api.headers)

    assert unsupported.status_code == 404
    assert unsupported.json()['code'] == 'fs_media_not_found'
    assert missing.status_code == 404
    assert missing.json()['code'] == 'fs_media_not_found'


def test_media_info_returns_the_duration_of_a_selected_source(api, monkeypatch):
    """El editor puede leer la duración de una fuente elegida fuera de out/."""
    source = api.tmp / 'source.wav'
    source.write_bytes(b'wav')
    monkeypatch.setattr(ffmpeg, 'probe_duration', lambda _path: 3.5)

    response = api.client.get('/fs/info', params={'path': str(source)}, headers=api.headers)

    assert response.status_code == 200
    assert response.json() == {'duration': 3.5, 'kind': 'audio', 'has_audio': True}


def test_media_info_assigns_default_duration_to_images(api):
    """Las imágenes se importan como clips visuales de cinco segundos por defecto."""
    source = api.tmp / 'logo.png'
    source.write_bytes(b'image')

    response = api.client.get('/fs/info', params={'path': str(source)}, headers=api.headers)

    assert response.status_code == 200
    assert response.json() == {'duration': 5.0, 'kind': 'image', 'has_audio': False}


def test_media_info_reports_video_audio_stream_for_linked_import(api, monkeypatch):
    """El cliente sabe cuándo debe enlazar el clip de audio con el video importado."""
    source = api.tmp / 'scene.mp4'
    source.write_bytes(b'video')
    monkeypatch.setattr(ffmpeg, 'probe_duration', lambda _path: 3.5)
    monkeypatch.setattr(ffmpeg, 'has_audio_stream', lambda _path: True)

    response = api.client.get('/fs/info', params={'path': str(source)}, headers=api.headers)

    assert response.status_code == 200
    assert response.json() == {'duration': 3.5, 'kind': 'video', 'has_audio': True}


def test_media_info_rejects_missing_or_unsupported_sources(api):
    """La lectura de duración no sirve rutas inexistentes ni archivos que no son medios."""
    text = api.tmp / 'notes.txt'
    text.write_text('text', encoding='utf-8')
    unsupported = api.client.get('/fs/info', params={'path': str(text)}, headers=api.headers)
    missing = api.client.get('/fs/info', params={'path': str(api.tmp / 'gone.wav')}, headers=api.headers)

    assert unsupported.status_code == 404
    assert missing.status_code == 404


def test_a_folder_that_does_not_exist_is_404(api):
    """Una carpeta que no existe responde 404 con su código del catálogo."""
    response = api.client.get(
        '/fs/list', params={'path': str(api.tmp / 'no-existe'), 'kinds': 'audio'}, headers=api.headers
    )

    assert response.status_code == 404
    assert response.json()['code'] == 'fs_path_not_found'

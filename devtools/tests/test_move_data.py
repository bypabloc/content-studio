"""AC-4: `move-data` mueve narration/ y music/ a server/data/ y reescribe las rutas de las instalaciones editables."""

from __future__ import annotations

import json

from devtools.move_data import main


def _arbol(root):
    (root / 'narration/voz').mkdir(parents=True)
    (root / 'narration/voz/clara.wav').write_bytes(b'RIFF')
    (root / 'music/models/heartlib').mkdir(parents=True)
    sitio = root / 'music/.venv-heartmula/Lib/site-packages'
    sitio.mkdir(parents=True)
    (sitio / '__editable__.heartlib-0.1.0.pth').write_text(str(root / 'music/models/heartlib') + '\n')
    info = sitio / 'heartlib-0.1.0.dist-info'
    info.mkdir()
    url = (root / 'music/models/heartlib').as_uri()
    (info / 'direct_url.json').write_text(json.dumps({'url': url, 'dir_info': {'editable': True}}))


def test_plan_sin_apply_no_toca_el_disco(tmp_path, capsys):
    _arbol(tmp_path)
    assert main(['--root', str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)['aplicado'] is False
    assert (tmp_path / 'narration/voz/clara.wav').is_file() and not (tmp_path / 'server').exists()


def test_apply_mueve_y_reescribe_pth_y_direct_url(tmp_path):
    _arbol(tmp_path)
    assert main(['--apply', '--root', str(tmp_path)]) == 0
    assert not (tmp_path / 'narration').exists() and not (tmp_path / 'music').exists()
    assert (tmp_path / 'server/data/narration/reference/clear.wav').is_file()  # paso 2: clara -> clear
    sitio = tmp_path / 'server/data/music/.venv-heartmula/Lib/site-packages'
    assert (sitio / '__editable__.heartlib-0.1.0.pth').read_text() == str(
        tmp_path / 'server/data/music/models/heartlib'
    ) + '\n'
    url = json.loads((sitio / 'heartlib-0.1.0.dist-info/direct_url.json').read_text())['url']
    assert url == (tmp_path / 'server/data/music/models/heartlib').as_uri()


def test_segunda_corrida_dice_ya_migrado(tmp_path, capsys):
    _arbol(tmp_path)
    main(['--apply', '--root', str(tmp_path)])
    capsys.readouterr()
    assert main(['--apply', '--root', str(tmp_path)]) == 0
    assert 'ya migrado' in capsys.readouterr().err


def test_colision_sale_1_sin_mover_nada(tmp_path):
    _arbol(tmp_path)
    (tmp_path / 'server/data/narration/voz').mkdir(parents=True)
    (tmp_path / 'server/data/narration/voz/clara.wav').write_bytes(b'otro')
    assert main(['--apply', '--root', str(tmp_path)]) == 1
    assert (tmp_path / 'narration/voz/clara.wav').is_file() and (tmp_path / 'music/models/heartlib').is_dir()
    assert (tmp_path / 'server/data/narration/voz/clara.wav').read_bytes() == b'otro'


def test_fusiona_en_un_destino_que_ya_tiene_versionado(tmp_path):
    """Tras el pull, server/data/narration/ ya tiene lo versionado: lo no versionado entra sin sobrescribir."""
    _arbol(tmp_path)
    (tmp_path / 'server/data/narration/docs').mkdir(parents=True)
    (tmp_path / 'server/data/narration/README.md').write_text('versionado')
    assert main(['--apply', '--root', str(tmp_path)]) == 0
    assert (tmp_path / 'server/data/narration/reference/clear.wav').is_file()
    assert (tmp_path / 'server/data/narration/README.md').read_text() == 'versionado'
    assert not (tmp_path / 'narration').exists()


def _arbol_nombres(root):
    """Tras el paso 1: los datos ya están en server/data/narration/ con los nombres viejos."""
    datos = root / 'server/data/narration'
    (datos / 'voz/tomas').mkdir(parents=True)
    (datos / 'voz/experta.wav').write_bytes(b'WAV1')
    (datos / 'voz/experta.txt').write_bytes(b'texto')
    (datos / 'voz/tomas/toma1.wav').write_bytes(b'TOMA')
    (datos / 'voces').mkdir()
    (datos / 'voces/catalogo.json').write_bytes(b'{"yesid": {}}')
    sitio = datos / 'motores/index-tts/.venv/Lib/site-packages'
    sitio.mkdir(parents=True)
    (sitio / '__editable__.index_tts-0.1.pth').write_text(str(datos / 'motores/index-tts') + '\n')
    (datos / 'docs/guiones').mkdir(parents=True)
    (datos / 'docs/guiones/guion.txt').write_bytes(b'guion')


def test_paso2_renombra_con_los_mismos_bytes_y_reescribe_engines(tmp_path):
    _arbol_nombres(tmp_path)
    assert main(['--apply', '--root', str(tmp_path)]) == 0
    datos = tmp_path / 'server/data/narration'
    assert (datos / 'reference/expert.wav').read_bytes() == b'WAV1'
    assert (datos / 'reference/expert.txt').read_bytes() == b'texto'
    assert (datos / 'reference/takes/toma1.wav').read_bytes() == b'TOMA'
    assert (datos / 'voices/catalog.json').read_bytes() == b'{"yesid": {}}'  # las claves las cambia git, no move-data
    assert (datos / 'docs/scripts/guion.txt').read_bytes() == b'guion'
    assert not (datos / 'voz').exists() and not (datos / 'voces').exists() and not (datos / 'docs/guiones').exists()
    assert not (datos / 'motores').exists()
    pth = datos / 'engines/index-tts/.venv/Lib/site-packages/__editable__.index_tts-0.1.pth'
    assert pth.read_text() == str(datos / 'engines/index-tts') + '\n'


def test_paso2_es_idempotente(tmp_path, capsys):
    _arbol_nombres(tmp_path)
    main(['--apply', '--root', str(tmp_path)])
    capsys.readouterr()
    assert main(['--apply', '--root', str(tmp_path)]) == 0
    assert 'ya migrado' in capsys.readouterr().err
    assert (tmp_path / 'server/data/narration/reference/expert.wav').read_bytes() == b'WAV1'


def test_paso2_colision_sale_1_sin_mover_nada(tmp_path):
    _arbol_nombres(tmp_path)
    (tmp_path / 'server/data/narration/reference').mkdir()
    (tmp_path / 'server/data/narration/reference/expert.wav').write_bytes(b'otro')
    assert main(['--apply', '--root', str(tmp_path)]) == 1
    datos = tmp_path / 'server/data/narration'
    assert (datos / 'voz/experta.wav').read_bytes() == b'WAV1'
    assert (datos / 'voces/catalogo.json').is_file() and (datos / 'motores/index-tts').is_dir()
    assert (datos / 'reference/expert.wav').read_bytes() == b'otro'

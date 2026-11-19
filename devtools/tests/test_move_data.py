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
    assert (tmp_path / 'server/data/narration/voz/clara.wav').is_file()
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


def test_destino_ocupado_sale_1_sin_mover_nada(tmp_path):
    _arbol(tmp_path)
    (tmp_path / 'server/data/narration').mkdir(parents=True)
    (tmp_path / 'server/data/narration/otra.txt').write_text('x')
    assert main(['--apply', '--root', str(tmp_path)]) == 1
    assert (tmp_path / 'narration/voz/clara.wav').is_file() and (tmp_path / 'music/models/heartlib').is_dir()

"""Un test por bug corregido del análisis. Corre con: uv run --with pytest pytest tests"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(RAIZ / 'narration'), str(RAIZ / 'music')]


def test_tomas_max_mas_uno(tmp_path):
    from content_studio.comun.archivos import siguiente_numero

    assert siguiente_numero(tmp_path, 'neutral') == 1
    for n in ['neutral-1', 'neutral-3', 'neutral-en-7', 'neutral-fin-9', 'neutral-x']:
        (tmp_path / f'{n}.wav').touch()
    assert siguiente_numero(tmp_path, 'neutral') == 4  # contando daba 6, y con huecos pisaba una toma


def test_musica_falla_sin_dejar_el_wav_viejo(tmp_path, monkeypatch):
    import pytest

    from content_studio.music import musica
    from content_studio.music.motores.base import EspecMusica, MotorMusica

    class Falla(MotorMusica):  # el motor "falla": no escribe nada
        def generar(self, trabajos, a):
            pass

    vieja = tmp_path / 'acestep-lofi-chill.wav'
    vieja.write_bytes(b'corrida anterior')
    monkeypatch.setattr(musica.proceso, 'usar_venv', lambda *a, **k: None)
    monkeypatch.setattr(EspecMusica, 'crear', lambda espec: Falla(espec))
    monkeypatch.setattr(sys, 'argv', ['musica.py', '--modelo', 'acestep', '--carpeta', str(tmp_path)])
    with pytest.raises(SystemExit) as e:
        musica.main()
    assert e.value.code and 'acestep-lofi-chill.wav' in str(e.value.code)
    assert not vieja.exists()


def test_tts_salida_carpeta_con_un_guion(tmp_path):
    from argparse import Namespace

    import pytest

    from content_studio.narration.guion import planificar

    a = Namespace(estilo=None, idioma='es', modelo='voxcpm2', salida=tmp_path)  # carpeta existente
    assert [s for *_, s in planificar(a, [('g', 'Hola', None)])] == [tmp_path / 'g-voxcpm2.wav']
    a.salida = tmp_path / 'toma.wav'
    assert [s for *_, s in planificar(a, [('g', 'Hola', None)])] == [a.salida]
    a.salida = tmp_path / 'toma.mp3'
    with pytest.raises(SystemExit):
        planificar(a, [('g', 'Hola', None)])


def test_tts_avisa_antes_de_sobrescribir(tmp_path, capsys):
    from content_studio.narration.guion import avisar_sobrescritura

    (tmp_path / 'a.wav').touch()
    avisar_sobrescritura([('t', 'experta', tmp_path / 'a.wav'), ('t', 'experta', tmp_path / 'b.wav')])
    err = capsys.readouterr().err
    assert 'a.wav' in err and 'b.wav' not in err


def test_help_en_cp1252():
    import os
    import subprocess

    env = {**os.environ, 'PYTHONIOENCODING': 'cp1252'}
    for args in (['music/musica.py', '--help'], ['cli.py', 'music', '--help']):
        r = subprocess.run([sys.executable, *args], cwd=RAIZ, env=env, capture_output=True)
        assert r.returncode == 0, r.stderr.decode('cp1252', 'replace')


def test_licencias_by_traen_atribucion():
    import voces

    sin = [n for n, f in voces.catalogo().items() if 'BY' in f['licencia'] and not voces.mencion(f)]
    assert not sin, f'licencia CC BY sin "atribucion" en catalogo.json: {sin}'

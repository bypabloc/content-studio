"""`studio mix` (spec 016, D-3): sin transcripción en caché o sin el archivo, sale con 2 y dice qué hacer."""

from __future__ import annotations

from content_studio.cli.main import main


def test_mix_refuses_a_voice_without_a_cached_transcript(tmp_path, capsys):
    """La voz debe estar transcrita (`studio clean`): sin caché, sale con 2 antes de crear nada."""
    voice = tmp_path / 'voice.wav'
    voice.write_bytes(b'RIFF')
    music = tmp_path / 'music.wav'
    music.write_bytes(b'RIFF')

    code = main(['mix', '--voice', str(voice), '--music', str(music), '--db', str(tmp_path / 'base.db')])

    assert code == 2
    assert 'studio clean' in capsys.readouterr().err


def test_mix_refuses_a_music_file_that_does_not_exist(tmp_path, capsys):
    """Un archivo que no existe sale con 2 y se nombra en el mensaje."""
    voice = tmp_path / 'voice.wav'
    voice.write_bytes(b'RIFF')
    missing = tmp_path / 'missing.wav'

    code = main(['mix', '--voice', str(voice), '--music', str(missing), '--db', str(tmp_path / 'base.db')])

    assert code == 2
    assert str(missing) in capsys.readouterr().err

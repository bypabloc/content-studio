"""Prueba de humo común de los motores TTS y de música."""

import subprocess
from pathlib import Path

from content_studio import paths
from content_studio.engines import recipes


def _verify(monkeypatch, tmp_path, engine, model_fails=False):
    from content_studio.engines import verification

    root = tmp_path / 'engines'
    monkeypatch.setattr(paths, 'engines_dir', lambda: root)
    monkeypatch.setenv('CONTENT_STUDIO_MODE', 'installed')
    recipe = recipes.load(engine)
    venv = root / engine / recipe.family / recipe.venv
    python = venv / 'Scripts' / 'python.exe'
    python.parent.mkdir(parents=True)
    python.touch()
    output = tmp_path / 'job-output'
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        if command[0] == str(python):
            if model_fails:
                return subprocess.CompletedProcess(command, 1, '', 'model failed')
            folder_flag = '--output' if '--output' in command else '--folder'
            folder = Path(command[command.index(folder_flag) + 1])
            folder.mkdir(parents=True, exist_ok=True)
            (folder / 'source.wav').write_bytes(b'RIFF test')
        elif command[0] == 'ffmpeg':
            Path(command[-1]).write_bytes(b'RIFF 1 second')
        elif command[0] == 'ffprobe':
            return subprocess.CompletedProcess(command, 0, '{"format":{"duration":"1.000000"}}', '')
        return subprocess.CompletedProcess(command, 0, '', '')

    monkeypatch.setattr(verification.subprocess, 'run', run)
    return verification.verify_engine(engine, output), calls


def test_tts_smoke_uses_the_consented_voice_and_trims_to_one_second(tmp_path, monkeypatch):
    result, calls = _verify(monkeypatch, tmp_path, 'qwen-0.6b')

    model_command = calls[0]
    assert '--voice' in model_command and model_command[model_command.index('--voice') + 1] == 'yesid'
    assert model_command[model_command.index('--text') + 1] == 'Prueba.'
    assert calls[1][calls[1].index('-t') + 1] == '1'
    assert result['ok'] is True
    assert result['duration_s'] == 1.0


def test_music_smoke_generates_five_seconds_then_trims_to_one(tmp_path, monkeypatch):
    result, calls = _verify(monkeypatch, tmp_path, 'acestep')

    model_command = calls[0]
    assert model_command[model_command.index('--duration') + 1] == '5'
    assert calls[1][calls[1].index('-t') + 1] == '1'
    assert result['ok'] is True
    assert result['duration_s'] == 1.0


def test_model_error_is_summarized_without_running_ffmpeg(tmp_path, monkeypatch):
    result, calls = _verify(monkeypatch, tmp_path, 'qwen-0.6b', model_fails=True)

    assert result['ok'] is False
    assert 'model failed' in result['error']
    assert len(calls) == 1


def test_missing_venv_returns_engine_not_installed(tmp_path, monkeypatch):
    from content_studio.engines import verification

    monkeypatch.setattr(paths, 'engines_dir', lambda: tmp_path / 'engines')
    monkeypatch.setenv('CONTENT_STUDIO_MODE', 'installed')

    result = verification.verify_engine('qwen-0.6b', tmp_path / 'verify')

    assert result['ok'] is False
    assert result['error'] == 'engine_not_installed'

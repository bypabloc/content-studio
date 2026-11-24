"""Prueba de humo común de los motores TTS y de música."""

import subprocess
from pathlib import Path

from content_studio import paths
from content_studio.common import process
from content_studio.engines import installer, recipes


def _verify(monkeypatch, tmp_path, engine, model_fails=False):
    from content_studio.engines import verification

    root = tmp_path / 'engines'
    monkeypatch.setattr(paths, 'engines_dir', lambda: root)
    monkeypatch.setenv('CONTENT_STUDIO_MODE', 'installed')
    recipe = recipes.load(engine)
    venv = installer.engine_venv(recipe, root)
    python = process.python_de(venv)
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
    assert calls[1][calls[1].index('-af') + 1] == 'apad=whole_dur=1'
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


def _assistant(tmp_path, monkeypatch):
    from content_studio.engines import verification

    monkeypatch.setattr(verification.paths, 'engines_dir', lambda: tmp_path)
    return verification


def test_assistant_model_is_verified_by_its_gguf_header(tmp_path, monkeypatch):
    """Spec 021: un modelo del asistente se verifica sin la GPU: su GGUF existe y empieza con la cabecera GGUF."""
    from content_studio.llm import models

    verification = _assistant(tmp_path, monkeypatch)
    assert verification.verify_engine('gemma-4-e4b', tmp_path / 'v')['ok'] is False
    gguf = models.gguf_path('gemma-4-e4b', tmp_path)
    gguf.parent.mkdir(parents=True)
    gguf.write_bytes(b'XXXX')
    assert 'not a GGUF' in verification.verify_engine('gemma-4-e4b', tmp_path / 'v')['error']
    gguf.write_bytes(b'GGUF' + b'0' * 8)
    assert verification.verify_engine('gemma-4-e4b', tmp_path / 'v') | {'checked_at': ''} == {
        'ok': True,
        'checked_at': '',
        'size_bytes': 12,
    }


def test_llama_cpp_is_verified_with_its_version(tmp_path, monkeypatch):
    """llama.cpp se verifica con `llama-server --version`."""
    from types import SimpleNamespace

    from content_studio.llm import models

    verification = _assistant(tmp_path, monkeypatch)
    assert verification.verify_engine('llama-cpp', tmp_path / 'v')['ok'] is False
    server = models.server_path(tmp_path)
    server.parent.mkdir(parents=True)
    server.write_bytes(b'')
    calls = []

    def run(command):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout='version: 12676 (abc)', stderr='')

    monkeypatch.setattr(verification, '_run', run)
    result = verification.verify_engine('llama-cpp', tmp_path / 'v')
    assert result['ok'] is True
    assert calls == [[str(server), '--version']]
    monkeypatch.setattr(verification, '_run', lambda command: SimpleNamespace(returncode=1, stdout='', stderr='boom'))
    assert verification.verify_engine('llama-cpp', tmp_path / 'v')['ok'] is False

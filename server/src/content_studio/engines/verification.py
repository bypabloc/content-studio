"""Prueba de humo de un segundo para los motores instalados."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from content_studio import paths
from content_studio.common import process, progress
from content_studio.engines import installer, recipes


def _checked_at() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _summary(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return '\n'.join(lines[-5:])[:1000] or 'The engine returned no error details.'


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        check=False,
        encoding='utf-8',
        errors='replace',
        env=process.env_src(),
        text=True,
    )


def _failure(error: str) -> dict:
    return {'ok': False, 'error': _summary(error), 'checked_at': _checked_at()}


def verify_engine(engine: str, output_dir: Path) -> dict:
    """Genera audio con el motor y confirma que FFmpeg puede dejarlo en un segundo."""
    recipe = recipes.load(engine)
    output_dir.mkdir(parents=True, exist_ok=True)
    python = process.python_de(installer.engine_venv(recipe, paths.engines_dir()))
    if not python.is_file():
        return _failure('engine_not_installed')

    source_dir = output_dir / 'source'
    source_dir.mkdir(exist_ok=True)
    if recipe.family == 'narration':
        source = source_dir / 'source.wav'
        command = [
            str(python),
            '-m',
            'content_studio.narration.tts',
            '--model',
            engine,
            '--voice',
            'yesid',
            '--style',
            'expert',
            '--text',
            'Prueba.',
            '--output',
            str(source),
        ]
    elif recipe.family == 'music':
        source = source_dir
        command = [
            str(python),
            '-m',
            'content_studio.music.music_main',
            '--model',
            engine,
            '--style',
            'lofi-chill',
            '--duration',
            '5',
            '--folder',
            str(source),
        ]
    else:
        return _failure(f'Unsupported engine family: {recipe.family}')

    try:
        progress.emit(0, 'loading model')
        generated = _run(command)
        if generated.returncode:
            return _failure(generated.stderr or generated.stdout)
        sources = [source] if source.is_file() else sorted(source.rglob('*.wav'))
        if not sources:
            return _failure('The engine finished without generating a WAV file.')

        audio = output_dir / 'verification.wav'
        progress.emit(0.8, 'trimming audio')
        trimmed = _run(
            [
                'ffmpeg',
                '-hide_banner',
                '-loglevel',
                'error',
                '-y',
                '-i',
                str(sources[0]),
                '-t',
                '1',
                '-c:a',
                'pcm_s16le',
                str(audio),
            ]
        )
        if trimmed.returncode:
            return _failure(trimmed.stderr or trimmed.stdout)

        probed = _run(
            [
                'ffprobe',
                '-v',
                'error',
                '-show_entries',
                'format=duration',
                '-of',
                'json',
                str(audio),
            ]
        )
        if probed.returncode:
            return _failure(probed.stderr or probed.stdout)
        duration = float(json.loads(probed.stdout)['format']['duration'])
        if not 0.95 <= duration <= 1.05:
            return _failure(f'Expected 1 second of audio; ffprobe reported {duration:.3f}.')
    except (KeyError, OSError, ValueError, subprocess.SubprocessError) as error:
        return _failure(str(error))

    progress.emit(1, 'verified')
    return {
        'ok': True,
        'checked_at': _checked_at(),
        'duration_s': round(duration, 3),
        'audio_path': str(audio),
    }

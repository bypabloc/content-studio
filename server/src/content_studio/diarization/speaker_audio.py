"""Audio de un hablante: el comando de ffmpeg que deja solo sus turnos y silencia el resto (spec 035, AC-5).

Stdlib solo: arma el comando; quien lo corre es el trabajo `diarize.split`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Más largo que esto, el filtro va en un archivo: la línea de comandos de Windows no lo admite.
MAX_INLINE_FILTER = 30_000


def _inside(turns: list[dict[str, Any]], speaker: str) -> str:
    """La expresión de ffmpeg que vale 1 dentro de cualquier turno del hablante; '0' si no tiene turnos."""
    spans = [f'between(t,{turn["start"]:.3f},{turn["end"]:.3f})' for turn in turns if turn['speaker'] == speaker]
    return '+'.join(spans) or '0'


def split_command(source: Path, turns: list[dict[str, Any]], speaker: str, out: Path) -> list[str]:
    """Comando de ffmpeg que deja `speaker` con su voz y silencia lo demás; mismo largo y frecuencia que `source`."""
    expression = f"volume=enable='not({_inside(turns, speaker)})':volume=0"
    command = ['ffmpeg', '-y', '-i', str(source)]
    if len(expression) <= MAX_INLINE_FILTER:
        command += ['-af', expression]
    else:
        script = out.with_name(f'{out.stem}.filter.txt')
        script.write_text(expression, encoding='utf-8')
        command += ['-filter_script:a', str(script)]
    return [*command, '-c:a', 'pcm_s16le', str(out)]

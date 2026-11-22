"""Render de audio del editor (spec 017, D-4): el documento se vuelve un grafo `filter_complex` puro, y ffmpeg lo corre.

Por clip: recorte de la fuente, fundidos, volumen (clip más pista) y el retardo hasta su `start`. Las pistas silenciadas
no entran; si hay alguna en solo, solo entran las que lo tienen. Todo suma con `amix` y se corta a la duración del
proyecto. El grafo va a un archivo (`-filter_complex_script`) para no chocar con el límite de la línea de comandos.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from content_studio.common import ffmpeg as ff
from content_studio.editor import project
from content_studio.editor.project import Doc
from content_studio.media import formats, normalize

# cspell:ignore amix adelay fltp STARTPTS: filtros y formatos de ffmpeg, que el diccionario no trae.


class RenderError(Exception):
    """Un render que no se puede hacer, con su código del catálogo."""

    def __init__(self, code: str, params: dict[str, Any] | None = None) -> None:
        """Guarda el código y sus parámetros."""
        super().__init__(code)
        self.code = code
        self.params = params or {}


@dataclass(frozen=True)
class Plan:
    """Las entradas de ffmpeg (en el orden de su `-i`) y el grafo que las mezcla."""

    inputs: list[Path]
    script: str


def build(doc: Doc, folder: Path) -> Plan:
    """El grafo del documento. Las fuentes relativas cuelgan de `folder`, la carpeta del proyecto.

    >>> build({'tracks': [], 'clips': []}, Path('.'))
    Traceback (most recent call last):
    ...
    content_studio.editor.render_audio.RenderError: nothing_to_render
    """
    audible = _audible_clips(doc)
    if not audible:
        raise RenderError('nothing_to_render')
    inputs: list[Path] = []
    lines: list[str] = []
    for index, (clip, track) in enumerate(audible):
        source = Path(clip['src'])
        source = source if source.is_absolute() else folder / source
        if source not in inputs:
            inputs.append(source)
        lines.append(_chain(clip, track, inputs.index(source), index))
    labels = ''.join(f'[c{index}]' for index in range(len(audible)))
    lines.append(f'{labels}amix=inputs={len(audible)}:normalize=0:dropout_transition=0[mix]')
    total = _num(project.duration(doc))
    lines.append(f'[mix]apad=whole_dur={total},atrim=end={total}[out]')
    return Plan(inputs, ';\n'.join(lines) + '\n')


def render(doc: Doc, folder: Path, out: Path, format: str = 'wav', normalize_preset: str | None = None) -> Path:
    """Renderiza el documento a `out` con el formato de audio `format`. Con `normalize_preset`, pasa por la 015.

    El grafo queda junto a la salida, en `<salida>.filter`.
    """
    target = formats.TARGETS.get(format)
    if target is None or target['kind'] != 'audio':
        raise RenderError('unknown_target', {'target': format})
    plan = build(doc, folder)
    script = out.with_suffix('.filter')
    script.write_text(plan.script, encoding='utf-8')
    if normalize_preset is None:
        _write(plan, script, out, target['codec'])
    else:
        raw = out.with_name(f'{out.stem}-raw.wav')
        _write(plan, script, raw, 'pcm_s16le')
        normalize.normalize(raw, out, target=normalize.target_lufs(normalize_preset))
        raw.unlink()
    return out


def _audible_clips(doc: Doc) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Los clips que suenan, con su pista: sin las silenciadas y, si hay solo, solo las que lo tienen."""
    tracks = {track['id']: track for track in doc['tracks']}
    soloed = {track['id'] for track in doc['tracks'] if track['solo']}
    return [
        (clip, tracks[clip['track']])
        for clip in doc['clips']
        if not tracks[clip['track']]['mute'] and (not soloed or clip['track'] in soloed)
    ]


def _chain(clip: dict[str, Any], track: dict[str, Any], number: int, index: int) -> str:
    """La cadena de un clip: recorte, fundidos, volumen y retardo, a la etiqueta `c<index>`."""
    steps = [
        f'[{number}:a]atrim=start={_num(clip["src_in"])}:end={_num(clip["src_out"])}',
        'asetpts=PTS-STARTPTS',
        f'aresample={project.SAMPLE_RATE}',
        'aformat=sample_fmts=fltp:channel_layouts=stereo',
    ]
    if clip['fade_in'] > 0:
        steps.append(f'afade=t=in:st=0:d={_num(clip["fade_in"])}')
    if clip['fade_out'] > 0:
        fade_start = project.clip_length(clip) - clip['fade_out']
        steps.append(f'afade=t=out:st={_num(fade_start)}:d={_num(clip["fade_out"])}')
    steps.append(f'volume={_num(clip["gain_db"] + track["volume_db"])}dB')
    steps.append(f'adelay={round(clip["start"] * 1000)}:all=1')
    return ','.join(steps) + f'[c{index}]'


def _num(value: float) -> str:
    """Un número para el grafo, sin ceros de más: `2`, `0.5`, `-6`.

    >>> [_num(2), _num(0.5), _num(-6.0), _num(10)]
    ['2', '0.5', '-6', '10']
    """
    return f'{value:.6f}'.rstrip('0').rstrip('.') or '0'


def _write(plan: Plan, script: Path, out: Path, codec: str) -> None:
    """Corre ffmpeg con el grafo del archivo `script`, sobre las entradas del plan, a `out` con su códec."""
    args: list[str] = []
    for path in plan.inputs:
        args += ['-i', str(path)]
    args += ['-filter_complex_script', str(script), '-map', '[out]', '-c:a', codec, str(out)]
    ff.ffmpeg('-y', *args)

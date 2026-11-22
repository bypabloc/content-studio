"""Subtítulos ASS (spec 014, D-3): clásico, redes con palabra resaltada y karaoke. Solo stdlib.

El server es la fuente del ASS para exportar y quemar; el client genera el mismo para la vista previa (D-9).
"""

from __future__ import annotations

from typing import Any

from content_studio.subtitles.segment import wrap_lines
from content_studio.subtitles.styles import ALIGNMENT, ass_color

# cspell:ignore fscx fscy centis Fontname Fontsize: etiquetas y campos de ASS.
LINE_CHARS = 42
POP = '\\t(0,80,\\fscx115\\fscy115)\\t(80,160,\\fscx100\\fscy100)'


def _time(seconds: float) -> str:
    """Tiempo de ASS, H:MM:SS.cc (centésimas)."""
    centis = round(seconds * 100)
    hours, rest = divmod(centis, 360_000)
    minutes, rest = divmod(rest, 6_000)
    secs, centis = divmod(rest, 100)
    return f'{hours}:{minutes:02d}:{secs:02d}.{centis:02d}'


def _text(word: str, style: dict[str, Any]) -> str:
    """Palabra sin llaves (las llaves son etiquetas de ASS) y en mayúsculas si el estilo lo pide."""
    cleaned = word.replace('{', '(').replace('}', ')')
    return cleaned.upper() if style['uppercase'] else cleaned


def _header(style: dict[str, Any], play_res: tuple[int, int]) -> list[str]:
    width, height = play_res
    fill = ass_color(style['color'])
    outline = ass_color(style['outline_color'])
    box = style['back_box']
    back = ass_color(box) if box else ass_color('#000000')
    border_style = 3 if box else 1
    bold = -1 if style['bold'] else 0
    return [
        '[Script Info]',
        'ScriptType: v4.00+',
        f'PlayResX: {width}',
        f'PlayResY: {height}',
        'WrapStyle: 0',
        'ScaledBorderAndShadow: yes',
        '',
        '[V4+ Styles]',
        'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, '
        'Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, '
        'MarginR, MarginV, Encoding',
        f'Style: Default,{style["font"]},{style["size"]},{fill},{fill},{outline},{back},{bold},0,0,0,100,100,0,0,'
        f'{border_style},{style["outline"]},{style["shadow"]},{ALIGNMENT[style["position"]]},40,40,'
        f'{style["margin_v"]},1',
        '',
        '[Events]',
        'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
    ]


def _dialogue(start: float, end: float, text: str) -> str:
    return f'Dialogue: 0,{_time(start)},{_time(end)},Default,,0,0,0,,{text}'


def _classic(cue: dict[str, Any], style: dict[str, Any]) -> str:
    lines = wrap_lines([_text(word, style) for word in cue['text'].split()], LINE_CHARS)
    return _dialogue(cue['start'], cue['end'], '\\N'.join(lines))


def _social(cue: dict[str, Any], style: dict[str, Any]) -> list[str]:
    """Un Dialogue por palabra activa: el cue entero, con esa palabra en el color de resaltado (o el de su palabra
    clave) y el pop; las demás, en el color del estilo."""
    fill = ass_color(style['color'])
    highlight = ass_color(style['highlight_color'])
    lines = []
    for active in cue['words']:
        parts = []
        for word in cue['words']:
            text = _text(word['text'], style)
            keyword = word.get('keyword')
            if word is active:
                color = ass_color(keyword['color']) if keyword and keyword.get('color') else highlight
                pop = POP if style['pop'] else ''
                text = f'{{\\c{color}{pop}}}{text}{{\\c{fill}}}'
            if keyword and keyword.get('emoji'):
                text = f'{text} {keyword["emoji"]}'
            parts.append(text)
        lines.append(_dialogue(active['start'], active['end'], ' '.join(parts)))
    return lines


def _karaoke(cue: dict[str, Any], style: dict[str, Any]) -> str:
    parts = []
    for word in cue['words']:
        centis = round((word['end'] - word['start']) * 100)
        parts.append(f'{{\\kf{centis}}}{_text(word["text"], style)}')
    return _dialogue(cue['start'], cue['end'], ' '.join(parts))


def to_ass(doc: dict[str, Any], style: dict[str, Any], play_res: tuple[int, int] = (1920, 1080)) -> str:
    """ASS del documento con el estilo dado. `play_res` es la resolución del video (o 1920×1080 si es solo audio)."""
    lines = _header(style, play_res)
    for cue in doc['cues']:
        if style['mode'] == 'social':
            lines.extend(_social(cue, style))
        elif style['mode'] == 'karaoke':
            lines.append(_karaoke(cue, style))
        else:
            lines.append(_classic(cue, style))
    return '\n'.join(lines) + '\n'

"""Tomas de un perfil (spec 010, D-3): cada toma es un WAV numerado por estilo; elegir una la copia a la referencia.

`takes/<estilo>/<n>.wav` son las tomas; `<estilo>.wav` y `<estilo>.txt` son la referencia elegida. La referencia que se
reemplaza no se pierde: pasa a `takes/` con el siguiente número.
"""

from __future__ import annotations

import shutil

from content_studio.narration import profiles, recording_kit


class TakeNotFound(Exception):
    """No hay una toma con ese número en el estilo."""


def _kit_style(style: str) -> str:
    """El estilo si es del kit; ValueError si no."""
    if style not in recording_kit.STYLES:
        raise ValueError(f'not a kit style: {style!r}')
    return style


def list_takes(profile: str, style: str) -> list[int]:
    """Números de las tomas del estilo, en orden."""
    return profiles.take_numbers(profile, _kit_style(style))


def save_take(profile: str, style: str, data: bytes) -> int:
    """Guarda `data` como la siguiente toma del estilo y devuelve su número."""
    number = max(list_takes(profile, style), default=0) + 1
    folder = profiles.takes_dir(profile, style)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f'{number}.wav').write_bytes(data)
    return number


def choose(profile: str, style: str, take: int) -> None:
    """Hace de la toma la referencia del estilo: la copia a `<estilo>.wav` y escribe el guion como `<estilo>.txt`.
    La referencia que se reemplaza pasa a `takes/`."""
    source = profiles.takes_dir(profile, _kit_style(style)) / f'{take}.wav'
    if not source.is_file():
        raise TakeNotFound(f'{profile}/{style}/{take}')
    chosen = profiles.reference_for(profile, style)
    if chosen.is_file():
        number = max(list_takes(profile, style), default=0) + 1
        shutil.move(str(chosen), str(profiles.takes_dir(profile, style) / f'{number}.wav'))
    shutil.copy2(source, chosen)
    profiles.reference_for(profile, style, '.txt').write_text(recording_kit.plain_text(style), encoding='utf-8')

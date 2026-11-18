"""Nombres de archivo."""

from __future__ import annotations

import re
from pathlib import Path


def siguiente_numero(carpeta: Path, prefijo: str) -> int:
    """Número de la toma siguiente: el mayor <prefijo>-<n>.wav más uno. Contar pisaba tomas con huecos, y el
    glob `neutral-*` también contaba `neutral-en-*`.

    >>> import tempfile
    >>> d = Path(tempfile.mkdtemp())
    >>> siguiente_numero(d, 'neutral')
    1
    >>> for n in ('neutral-1', 'neutral-3', 'neutral-en-7', 'neutral-fin-9'): _ = (d / f'{n}.wav').write_bytes(b'')
    >>> siguiente_numero(d, 'neutral')
    4
    """
    return (
        max(
            (
                int(m[1])
                for p in carpeta.glob(f'{prefijo}-*.wav')
                if (m := re.fullmatch(rf'{re.escape(prefijo)}-(\d+)', p.stem))
            ),
            default=0,
        )
        + 1
    )

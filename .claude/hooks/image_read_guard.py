"""PreToolUse (Read): solo el agente `image-reader` (Haiku) abre imágenes.

Un espectrograma o una captura leídos en la ventana principal gastan muchos tokens; `image-reader`
los describe en texto. `agent_type` solo viene en llamadas de un subagente. Exit 2 bloquea y avisa.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

IMAGES = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.avif', '.tif', '.tiff'}
AGENT = 'image-reader'


def blocked(path: str, agent: str | None) -> bool:
    """True si `agente` no puede leer `ruta` por ser una imagen.

    >>> blocked('out/spec.png', None), blocked('out/spec.PNG', 'image-reader'), blocked('a.wav', None)
    (True, False, False)
    """
    return Path(path).suffix.lower() in IMAGES and agent != AGENT


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    if blocked(data.get('tool_input', {}).get('file_path', ''), data.get('agent_type')):
        print(f'image_read_guard: blocked; delegate the image to the agent {AGENT} (Haiku)', file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()

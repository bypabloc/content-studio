"""PreToolUse (Read): solo el agente `image-reader` (Haiku) abre imágenes.

Un espectrograma o una captura leídos en la ventana principal gastan muchos tokens; `image-reader`
los describe en texto. `agent_type` solo viene en llamadas de un subagente. Exit 2 bloquea y avisa.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

IMAGENES = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.avif', '.tif', '.tiff'}
AGENTE = 'image-reader'


def bloqueado(ruta: str, agente: str | None) -> bool:
    """True si `agente` no puede leer `ruta` por ser una imagen.

    >>> bloqueado('out/spec.png', None), bloqueado('out/spec.PNG', 'image-reader'), bloqueado('a.wav', None)
    (True, False, False)
    """
    return Path(ruta).suffix.lower() in IMAGENES and agente != AGENTE


def main() -> None:
    try:
        datos = json.load(sys.stdin)
    except Exception:
        return
    if bloqueado(datos.get('tool_input', {}).get('file_path', ''), datos.get('agent_type')):
        print(f'image_read_guard: bloqueado; delega la imagen al agente {AGENTE} (Haiku)', file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()

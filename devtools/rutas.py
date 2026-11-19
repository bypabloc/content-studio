"""Raíz del checkout para los devtools. Solo stdlib: no importa el paquete content_studio.

>>> (RAIZ / 'cli.py').is_file()
True
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

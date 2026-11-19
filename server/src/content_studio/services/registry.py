"""Servicios por tipo de trabajo: la API, el worker y el CLI usan los mismos (spec 004, D-2)."""

from content_studio.services import music, narration

SERVICES = {'narration': narration, 'music': music}

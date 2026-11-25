"""Paleta y nombre inicial de los hablantes (spec 035, D-6 y «3. Datos»)."""

from __future__ import annotations

from content_studio.messages import t

PALETTE = ('#2563eb', '#dc2626', '#16a34a', '#d97706', '#9333ea', '#0891b2', '#db2777', '#65a30d')


def color(index: int) -> str:
    """Color del hablante número `index` (desde 0); la paleta se repite después del octavo."""
    return PALETTE[index % len(PALETTE)]


def default_name(number: int) -> str:
    """Nombre inicial de un hablante numerado desde 1, en el idioma por defecto del catálogo."""
    return t('speakers.default_name', n=number)


def build(speaker_ids: list[str]) -> dict[str, dict[str, str]]:
    """Nombre y color iniciales de cada hablante, en el orden en que pyannote los entrega."""
    return {
        speaker: {'name': default_name(index + 1), 'color': color(index)} for index, speaker in enumerate(speaker_ids)
    }

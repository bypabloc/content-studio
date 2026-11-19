"""POST /narration/lint: avisos del linter del guion, con su texto, más las palabras y la duración (spec 006, D-1)."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel

from content_studio.messages import t
from content_studio.narration import script_lint

router = APIRouter()


class ScriptIn(BaseModel):
    """El guion tal como lo escribe el usuario, y el estilo para estimar su duración."""

    text: str
    style: str = 'expert'


@router.post('/narration/lint')
def lint(body: ScriptIn) -> dict:
    """Incidencias con línea, columna y largo, cada una con el texto de su regla; también palabras y segundos."""
    issues = script_lint.lint(body.text)
    return {
        'issues': [{**asdict(issue), 'message': t(f'lint.rule_{issue.rule}', **issue.params)} for issue in issues],
        'words': script_lint.words(body.text),
        'seconds': script_lint.estimate_seconds(body.text, body.style),
        'guide': script_lint.GUIDE,
    }

"""POST /narration/lint: avisos del linter del guion, con su texto, más las palabras y la duración (spec 006, D-1)."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from content_studio.messages import t
from content_studio.narration import script_lint

router = APIRouter()
LINT_MAX_CHARS = 20_000  # unos 20 minutos de narración: más largo, las expresiones del linter tardan demasiado


class ScriptIn(BaseModel):
    """El guion tal como lo escribe el usuario, y el estilo para estimar su duración."""

    text: str = Field(max_length=LINT_MAX_CHARS)
    style: str = 'expert'


class IssueOut(BaseModel):
    """Un aviso del linter: la regla de formato-guion.md, su posición (1-based) y su texto ya en español."""

    rule: int
    code: str
    line: int
    col: int
    length: int
    params: dict[str, Any]
    message: str


class LintOut(BaseModel):
    """Lo que devuelve el lint: los avisos, las palabras, los segundos estimados y la guía de formato."""

    issues: list[IssueOut]
    words: int
    seconds: float
    guide: str


@router.post('/narration/lint', response_model=LintOut)
def lint(body: ScriptIn) -> dict:
    """Incidencias con línea, columna y largo, cada una con el texto de su regla; también palabras y segundos."""
    issues = script_lint.lint(body.text)
    return {
        'issues': [{**asdict(issue), 'message': t(f'lint.rule_{issue.rule}', **issue.params)} for issue in issues],
        'words': script_lint.words(body.text),
        'seconds': script_lint.estimate_seconds(body.text, body.style),
        'guide': script_lint.GUIDE,
    }

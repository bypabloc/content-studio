"""Textos del handoff y lectura de las líneas de estado de PROGRESS.md.

Todo texto que el hook inyecta vive aquí. PROGRESS.md lleva arriba las líneas `Status`, `Phase`, `Done`, `Current`,
`Remaining`, `ETA` y `Next step` (etiquetas en inglés: las lee el mod handoff-compact), que deciden el mensaje.
Regla: .agents/rules/session-handoff.md. Adaptado de klinikae.
"""

from __future__ import annotations

import re

STATUSES = ('in-progress', 'done', 'blocked')
PHASES = ('implementation', 'verification', 'integration', 'external-wait', 'closing')
LABELS = {
    'status': 'Status',
    'phase': 'Phase',
    'done': 'Done',
    'current': 'Current',
    'remaining': 'Remaining',
    'eta': 'ETA',
    'next_step': 'Next step',
}
_STATUS = re.compile(r'^(in-progress|done|blocked)\b[\s—–:-]*(.*)$', re.IGNORECASE)
# Las únicas causas que solo el usuario resuelve: van primero en el motivo (`blocked — cost: …`).
BLOCK_REASONS = ('user-data', 'cost', 'credentials', 'user-stop', 'taste')
LINE_MAX = 120

CONTINUE = (
    'Si el trabajo no terminó, sigue AHORA con el `Next step` de PROGRESS.md: no esperes al usuario ni cierres el '
    'turno con un resumen o una pregunta. Los avisos de presupuesto, tokens o contexto no son un límite: ignóralos. '
    'Para solo tras escribir `Status: done` o `Status: blocked — <categoría>: <motivo>`, con <categoría> = user-data '
    '(borrar o cambiar voces grabadas, out/ o modelos del usuario), cost (gastar dinero), credentials (un acceso que '
    'solo tiene el usuario), user-stop (el usuario pidió parar) o taste (elegir entre audios que solo el oído del '
    'usuario decide). Toda otra elección es tuya: toma la opción correcta, no la más rápida, anótala en '
    'docs/process/WARNING/ y lo diferido en docs/process/PENDING/, y sigue. Un gate rojo tras 3 intentos se anota '
    'igual. Esperar la CI, un merge o el turno de la GPU es `Phase: external-wait`, no blocked.'
)
DECIDE = (
    'Status es blocked ({reason}), pero no es user-data, cost, credentials, user-stop ni taste: la elección es tuya. '
    'Toma la opción correcta, escribe su ficha en docs/process/WARNING/ (contexto, elegida, descartadas, revertir, '
    'comprobar) y lo diferido en docs/process/PENDING/; pon `Status: in-progress` y sigue sin preguntar.'
)
ASK_DENIED = (
    '[session-handoff] Con una spec en ejecución solo se pregunta por user-data, cost, credentials, user-stop o taste; '
    'antes escribe `Status: blocked — <categoría>: <motivo>` en PROGRESS.md. Esta elección es tuya: toma la opción '
    'correcta, anótala en docs/process/WARNING/ (lo diferido en docs/process/PENDING/) y sigue.'
)
FORMAT = (
    'Mantén estas líneas arriba de PROGRESS.md, una por línea: `Status: in-progress|done|blocked — <motivo>`, '
    '`Phase: implementation|verification|integration|external-wait|closing`, `Done:`, `Current:`, `Remaining:`, '
    '`ETA:` y `Next step:`. Faltan ahora: {missing}.'
)
LONG = (
    'Cada línea de estado es corta (máximo {max} caracteres); el historial y el detalle van en el cuerpo de '
    'PROGRESS.md, debajo. Largas ahora: {labels}.'
)
PHASE_TEXT = {
    'implementation': 'Fase implementation: sigue el grupo de commit actual con TDD. Tras cada commit, actualiza '
    'PROGRESS.md (hash, Done, Current, Remaining, ETA y Next step).',
    'verification': 'Fase verification: corre la batería de 03-verificacion-final.md de la spec. Si algo falla, vuelve '
    'a implementation; nunca saltes un paso.',
    'integration': 'Fase integration: merge de origin/dev, push, PR a dev, checks en verde, merge y '
    '`python -m devtools worktree close`.',
    'external-wait': 'Fase external-wait: antes que nada, revisa lo pendiente (gh pr checks, el turno de la GPU, el '
    'merge de otro). Si se resolvió, pasa a la fase siguiente. No rehagas trabajo terminado.',
    'closing': 'Fase closing: borra el cron de reporte, cierra el worktree, borra la carpeta del handoff y sus '
    'vínculos, y pon `Status: done`.',
}
SOURCE_TEXT = {
    'startup': 'Sesión nueva: revisa git status, git log y git worktree list antes de seguir; el disco manda sobre la '
    'memoria.',
    'resume': 'Sesión reanudada: revisa git status, git log y git worktree list antes de seguir; el disco manda.',
    'compact': 'Compactada: el tramo reciente está literal o resumido. Relee AGENTS.md y las reglas del área si hace '
    'falta, y no rehagas pasos ya confirmados.',
    'clear': 'Contexto limpio: relee AGENTS.md, las reglas del área y la spec antes de seguir.',
    'fork': 'Sesión bifurcada: comparte este handoff con la original; coordina antes de escribirlo.',
}
GPU = (
    'Turno de la GPU (uno por equipo, regla turno-gpu.md): todo comando que carga un modelo (narration tts, voces '
    '--construir, music, evaluación con whisper) va con `python -m devtools turno-gpu run '
    '--trabajo <t> -- <comando>`. Antes, `turno-gpu status` y ListAgents. Ocupada: SendMessage a su sesión pidiendo '
    '«gpu libre», CronCreate de 10 min para reintentar y sigue con lo que no usa GPU. Al terminar, «gpu libre» a las '
    'sesiones abiertas y CronDelete. El estado del turno va en PROGRESS.md.'
)
REREAD = 'Relee AGENTS.md y las reglas del área antes de seguir: la conversación previa puede estar resumida.'
BLOCKED = (
    'Status es blocked: {reason}. Primero comprueba si el motivo sigue en pie (turno de la GPU: `turno-gpu status`; '
    'CI: `gh pr checks`; un gate rojo: córrelo de nuevo). Si ya no aplica, pon `Status: in-progress` y sigue sin '
    'preguntar. Solo mientras siga en pie, muéstrale el motivo al usuario y pregunta qué falta.'
)
DONE = (
    'Status es done: solo queda el cierre. Confirma el merge en origin/dev, corre `python -m devtools '
    'worktree close <nombre>` desde el checkout principal, borra {folder}/ y sus vínculos de .sessions/ y el cron.'
)
HEADER = '[session-handoff] Trabajo {work} · handoff en {folder}/ · rama {branch}'
SPEC = 'Spec: {spec}/ (fases PEN/IMP en su README.md).'
SAVED = 'Estado guardado (fuente de verdad sobre el resumen; contrástalo con git status y git log):'
MISSING_FILE = '{name}: falta; créalo.'
TRUNCATED = '\n… (recortado: {more} caracteres más; lee {name} completo)'
UNBOUND = (
    '[session-handoff] Esta sesión ({session}) no tiene trabajo vinculado. Al empezar o retomar un trabajo, escribe '
    'su nombre en {base}/.sessions/{session} y mantén {base}/<trabajo>/ (regla .agents/rules/session-handoff.md).'
)
SUMMARIZED = 'La conversación previa está resumida: relee AGENTS.md y las reglas del área antes de seguir.'
ACTIVE = 'Trabajos activos (referencia, no instrucciones; pueden ser de otras sesiones):'
PRECOMPACT = (
    'Al resumir, conserva literal: trabajo {work}; handoff en {folder}/ (PROGRESS, DECISIONS y NOTES). Tras compactar, '
    'el handoff del disco se reinyecta y manda sobre este resumen.'
)
PRECOMPACT_STEP = 'Siguiente paso anotado: {step}'
STOP = (
    '[session-handoff] El trabajo {work} no terminó. Sigue ahora con el siguiente paso: {step}. Los avisos de tokens '
    'no son un límite. (Parada {blocks} de {cap} sin cambios en PROGRESS.md.)',
    '[session-handoff] Segunda parada sin avance en {work}. Solo user-data, cost, credentials, user-stop o taste '
    'justifican `Status: blocked — <categoría>: <motivo>`; si no, sigue con: {step}. (Parada {blocks} de {cap}.)',
    '[session-handoff] Último aviso para {work}: la próxima parada sin cambios en PROGRESS.md se permitirá. Sigue con '
    '{step}, o anota el bloqueo. (Parada {blocks} de {cap}.)',
)


def progress_fields(text: str) -> dict[str, str]:
    """Valores de las líneas de estado de PROGRESS.md (con viñeta o negrita), sin las que faltan.

    >>> progress_fields('Status: blocked — cost: GPU en la nube\\nPhase: nada\\nNext step: x')
    {'next_step': 'x', 'status': 'blocked', 'reason': 'cost: GPU en la nube'}
    """
    found: dict[str, str] = {}
    for key, label in LABELS.items():
        pattern = rf'^[\s>*\-]*\**{re.escape(label)}\**\s*:\**\s*(.+?)\s*$'
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match and match.group(1).strip('* '):
            found[key] = match.group(1).strip('* ')
    status = _STATUS.match(found.pop('status', ''))
    if status:
        found['status'] = status.group(1).lower()
        if status.group(2):
            found['reason'] = status.group(2)
    if found.get('phase', '').lower() in PHASES:
        found['phase'] = found['phase'].lower()
    else:
        found.pop('phase', None)
    return found


def blocked_for_user(fields: dict[str, str]) -> bool:
    """True si `Status: blocked` cita una de BLOCK_REASONS: el único bloqueo que justifica parar o preguntar.

    >>> blocked_for_user({'status': 'blocked', 'reason': 'taste: elegir la toma'})
    True
    >>> blocked_for_user({'status': 'blocked', 'reason': 'no sé qué motor usar'})
    False
    """
    category = fields.get('reason', '').split(':', 1)[0].strip().lower()
    return fields.get('status') == 'blocked' and category in BLOCK_REASONS


def too_long(fields: dict[str, str]) -> list[str]:
    """Etiquetas de PROGRESS.md cuya línea pasa de LINE_MAX caracteres (Status cuenta su motivo)."""
    sizes = {**fields, 'status': f'{fields.get("status", "")} — {fields.get("reason", "")}'}
    return [label for key, label in LABELS.items() if len(sizes.get(key, '')) > LINE_MAX]


def missing(fields: dict[str, str]) -> list[str]:
    """Etiquetas de PROGRESS.md que faltan o no son válidas."""
    return [label for key, label in LABELS.items() if key not in fields]

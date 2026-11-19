# handoff-compact

Mod de Claude Code (2.1.287 o posterior), traído de klinikae, que reemplaza el resumen de la compactación por el handoff en disco (`tmp/handoff/<trabajo>/`, regla `session-handoff.md`).

## Qué hace

Atiende `session.compact` (`/compact`, el umbral automático del 60 % o un plugin):

| Caso | Resultado |
| :--- | :--- |
| Sesión con trabajo vinculado | No llama al modelo. Deja un aviso y los mensajes más recientes que caben en ~20k tokens, cortados en un punto seguro (ningún resultado de herramienta queda sin su llamada). Los turnos anteriores al último pedido del usuario se devuelven sin `thinking` ni reglas anidadas (`slim` en `hooks/tail.ts`). El handoff entra después por `SessionStart` `compact`. Tarda ~0,1 s. |
| Sin trabajo vinculado, subagente o ningún corte seguro (`tail-too-big`) | `next(e)`: Claude Code compacta como siempre, con `PreCompact` y el resumen del modelo. |
| `precompute` | Se omite. |

Para saber si hay trabajo vinculado, ejecuta `.agents/hooks/session_handoff.py` (con `uv run --no-project python`, que funciona en Windows y en WSL) con la entrada de `SessionStart` `compact`. Cada decisión (`compact.kept` o `compact.fallback`) queda en `tmp/handoff/.log/events.jsonl`.

### Estado del trabajo a la vista

Lee las líneas de estado de `PROGRESS.md` con `session_handoff.py --status` al iniciar, en cada prompt, al cerrar el turno y tras cada `Write` o `Edit`:

| Dónde | Qué muestra |
| :--- | :--- |
| Spinner | `<Phase> · <Current> · ETA <ETA>` en lugar de la palabra animada |
| Banda sobre el prompt | Estado, fase, ETA (y el motivo si está `blocked`) y `ctx <n>%` de la ventana de contexto. `Hide` la oculta en la sesión |

## Instalación

Está declarado en `.claude/settings.json` (`extraKnownMarketplaces.content-studio` con la carpeta `./.claude/mods` y `enabledPlugins["handoff-compact@content-studio"]`). Al abrir el repo, Claude Code ofrece instalarlo. A mano:

```bash
claude plugin install handoff-compact@content-studio --scope project
```

Tras editar el mod, `/reload-plugins` lo vuelve a leer.

## Probar

```bash
claude plugin validate .claude/mods/handoff-compact
claude plugin test .claude/mods/handoff-compact       # tests de tail.ts y status.ts
```

## Límites

* Solo en Claude Code: Codex y Antigravity siguen con su compactación y el hook de `.agents/hooks.json`.
* En el camino del mod no corre `PreCompact`; sí `PostCompact` y `SessionStart` `compact`.
* El tamaño se estima en caracteres (~4 por token). Lo que no esté en el handoff ni en el tramo reciente se pierde: mantén `PROGRESS.md` al día.

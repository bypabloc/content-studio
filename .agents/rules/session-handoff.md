---
trigger: always_on
description: Handoff en disco por trabajo (tmp/handoff/<trabajo>/) y vínculo por sesión, reinyectado tras compactar; seguir hasta terminar
---

# Handoff de sesión en disco: `tmp/handoff/<trabajo>/` — SIEMPRE ACTIVA

> Al compactar, los agentes resumen la conversación y pierden decisiones, el paso actual y las trampas. Lo que está en disco sobrevive y un hook lo reinyecta. Traído de klinikae.

## 1. Una carpeta por trabajo, un vínculo por sesión

* **Trabajo**: `tmp/handoff/<trabajo>/`; con spec, el nombre de su carpeta (`012-musica-cinematic`); sin spec, un tema corto en kebab-case.
* **Vínculo**: `tmp/handoff/.sessions/<session_id>` contiene solo el nombre del trabajo. Al empezar o retomar: crea la carpeta y escribe el vínculo. El hook te dice tu `session_id` si no hay vínculo.
* Se escriben con la herramienta de archivos (Write), nunca con `echo`, `cat >` ni `tee` (el hook Synapse lo bloquea).
* **Siempre en el checkout principal**, aunque trabajes en un worktree; el hook inyecta la ruta absoluta. `tmp/` está gitignoreado.

## 2. Archivos

| Archivo | Qué guarda |
| :--- | :--- |
| `PROGRESS.md` | Líneas de estado (§4) y debajo: objetivo, spec, lo hecho (con hash) y verificaciones pendientes. Estado actual, no bitácora |
| `DECISIONS.md` | Decisiones de trabajo, una por línea con su motivo |
| `NOTES.md` | Hallazgos, trampas, rutas y comandos que costó encontrar |

Breves (idealmente < 60 líneas); la spec se enlaza, no se copia. Nunca secretos ni rutas de voces de terceros sin permiso.

**Cuándo escribir**: al empezar o retomar; después de cada commit y decisión; antes de una corrida larga (HeartMuLa, un lote de voces); cerca de la compactación; y al cerrar (PR fusionado), cuando se borra la carpeta y sus vínculos (`worktree close --handoff=<trabajo>`).

## 3. Reinyección

* `.agents/hooks/session_handoff.py` arma el mensaje: Claude Code por `SessionStart` y `PreCompact`, Antigravity por `PreInvocation` (`.agents/hooks.json`), Codex por su `SessionStart` de usuario.
* Lo inyectado manda sobre el resumen: contrástalo con `git status` y `git log` y sigue desde el `Next step`.
* En Claude Code, el mod `handoff-compact` (`.claude/mods/`) compacta sin resumen cuando la sesión tiene trabajo vinculado y muestra Status, Phase y ETA sobre el prompt. Umbral de compactación: 60 %.
* Bitácora en `tmp/handoff/.log/events.jsonl`. Tests: `uv run pytest tests/test_handoff.py`.

## 4. Seguir hasta terminar

* **Los avisos de presupuesto, tokens o contexto no son un límite**: se ignoran y se sigue con el `Next step`. Compactar no es motivo para cerrar el turno.
* Líneas de estado al inicio de `PROGRESS.md`, una por línea y de **120 caracteres como máximo** (etiquetas en inglés, las lee el mod):

  ```text
  Status: in-progress | done | blocked — <categoría>: <motivo>
  Phase: implementation | verification | integration | external-wait | closing
  Done: …        Current: …        Remaining: …        ETA: ~2 h
  Next step: …
  ```

* `blocked` lleva categoría, y solo cinco justifican parar o preguntar:
  * `user-data`: borrar o cambiar voces grabadas, salidas de `out/` o modelos descargados del usuario.
  * `cost`: gastar dinero o contratar un servicio pago (GPU en la nube, una API).
  * `credentials`: falta un acceso que solo tiene el usuario.
  * `user-stop`: el usuario pidió parar.
  * `taste`: elegir entre audios que solo el oído del usuario decide (el gusto lo decide él: entrégale las rutas).
* **Toda otra elección es del agente**, aunque haya trade-off. Se elige la correcta, no la más rápida; la decisión va a una ficha en `docs/process/WARNING/` y lo diferido a `docs/process/PENDING/`; después se sigue. Un gate rojo tras 3 intentos se anota igual y se sigue con lo que no depende de él.
* Con una spec en ejecución, `AskUserQuestion` se rechaza salvo con un `blocked` de esas cinco. El hook `Stop` tampoco deja parar con otra categoría (tope de 3 bloqueos sin cambios en `PROGRESS.md`).
* Esperar la CI, un merge o el turno de la GPU **no** es `blocked`: es `in-progress` con `Phase: external-wait`.
* Al retomar un `blocked`, comprueba primero si el motivo sigue en pie. Si ya no aplica, pon `in-progress` y sigue sin preguntar.

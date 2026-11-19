---
trigger: model_decision
description: Validación conductual de cambios en instrucciones de agentes (.agents/, .claude/, AGENTS.md) y sincronía entre las dos copias de cada regla
---

# Validar cambios en las instrucciones de agentes

Al modificar `.agents/`, `.claude/` o `AGENTS.md`, valida que el agente disponible aplique la instrucción y responda con fidelidad. Leer el archivo no es evidencia.

* **Dos copias, un cuerpo**: cada regla vive en `.agents/rules/<regla>.md` (frontmatter `trigger` y `description`, para Antigravity y otros agentes) y en `.claude/rules/<regla>.md` (frontmatter opcional `paths:` de Claude Code). El cuerpo es idéntico y lo comprueba `tests/validators/test_structure.py`. Lo mismo con cada skill en `.agents/skills/` y `.claude/skills/`. Se edita la fuente de `.agents/` y se copia con `python -m devtools rules --sync`, que conserva el frontmatter de `.claude/`; las dos van en el mismo commit.
* Excepción: `claude-config-testing.md` es solo de Claude Code (su comando headless) y este archivo es su versión general.
* **Validación**: con el CLI del agente en modo no interactivo, sin web ni MCP, prompts en español que pregunten un **hecho discriminante** (algo que el modelo no adivinaría: `../content-studio-worktrees/`, `gpu-turn run`, la categoría `taste`, el tope de 300 líneas). Por regla: una tarea general, una trampa (que la regla debe rechazar) y un negativo (pregunta ajena que no debe arrastrar la regla).
* Resultados en `tmp/config-tests/<tema>.json` y el resumen `N/N PASS` en el cuerpo del commit.
* El tamaño de lo que carga cada agente lo mide `python -m devtools agent-context` (lo corre el `pre-commit`): una regla de más de 15 000 caracteres se recorta y su detalle va a `docs/`.
* No presupongas que la configuración de un CLI (modelos, permisos, hooks de `.claude/settings.json`) vincula a otros agentes.

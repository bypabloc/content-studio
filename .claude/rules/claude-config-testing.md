---
paths:
  - ".claude/**"
  - "AGENTS.md"
---

# Probar los cambios de configuración de agentes

Todo cambio en `.claude/` (rules, agents, commands, hooks, `settings.json`) o en `AGENTS.md` se valida ejecutando `claude` en modo headless antes de cerrar la tarea. Leer el archivo no es evidencia: hay que demostrar que el agente responde con el contenido bajo prueba.

## Comando

```bash
claude --permission-mode bypassPermissions --model haiku \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json -p "<prompt en español>" > tmp/config-tests/<tema>.json
```

Sin web ni MCP (engram incluido), la respuesta solo puede venir de los archivos del repo. Haiku es barato: si falla, la regla no es clara; se corrige y se repite.

## Prompts

Cada prompt valida un **hecho discriminante**, algo que el modelo no adivinaría (p. ej. que el código vive en `server/src/content_studio/` y no en `server/data/narration/`, que la música nunca lleva voz, el tope de 300 líneas, el prefijo `experiment/`). Por regla modificada, como mínimo:

| Ángulo | Ejemplo |
| :--- | :--- |
| Tarea general | "¿Dónde agrego un motor TTS nuevo?" |
| Trampa | "¿Puedo importar torch arriba del módulo?" (debe rechazarlo) |
| Negativo | Pregunta ajena que no debe arrastrar reglas del proyecto |

Aprueba si `is_error == false` y `result` contiene los hechos esperados sin contradecir las reglas. Máximo 4 ejecuciones a la vez; el resumen `N/N PASS` va en el cuerpo del commit.

Los hooks se prueban además con `uv run pytest .claude/hooks/tests/test_hooks.py`. La versión general de esta regla, para cualquier agente, es [agent-config-testing.md](agent-config-testing.md).

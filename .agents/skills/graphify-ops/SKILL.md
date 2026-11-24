---
name: graphify-ops
description: >
  Instala, construye y mantiene el grafo de graphify de content-studio: primer build, refresco, diagnóstico y
  benchmark. SIEMPRE invocar ANTES de correr un comando de graphify que ESCRIBE (update, cluster-only, label, --force)
  y ANTES de diagnosticar por qué el grafo falta, está viejo o vacío. NUNCA borrar graphify-out/ ni correr
  `graphify update --force` sin esta skill. Usar cuando el usuario diga "instalar graphify", "generar el grafo",
  "actualizar el grafo", "grafo desactualizado", "refused to shrink", "grafo vacío", "cuánto ahorra".
allowed-tools: Read, Glob, Bash(graphify:*), Bash(git:*), Bash(uv tool:*)
argument-hint: "install | update | fresh | diagnose | benchmark"
---

# Graphify ops

Todo lo que escribe en `graphify-out/` (gitignoreado, artefacto local). Para consultar: skill `graphify-query`. Regla: `.agents/rules/graphify.md`.

## Instalación y primer build (una vez por equipo y sistema)

```bash
uv tool install graphifyy        # CLI `graphify` en ~/.local/bin (paquete PyPI "graphifyy"); en Windows y en WSL por separado
graphify update .                # AST puro: sin LLM ni API key, segundos
graphify diagnose multigraph     # salud: missing/dangling en 0
```

Desde ahí los hooks (`graphify_update.py` en SessionStart y PostToolBatch) lo mantienen fresco.

## Comandos por tarea

| Tarea | Comando |
| :--- | :--- |
| Verificar frescura | `git rev-parse --short HEAD` y `Built from` en `graphify-out/GRAPH_REPORT.md` |
| Refrescar tras cambios de código | `graphify update .` |
| Refrescar tras **borrar** código ("refused to shrink") | `graphify update . --force` (antes, `git log --stat` confirma que el código se redujo) |
| Comunidades mal agrupadas | `graphify cluster-only . --no-viz --no-label` |
| Integridad | `graphify diagnose multigraph` |
| Ahorro de tokens | `graphify benchmark` |
| Lock huérfano tras un crash | borra la carpeta vacía `graphify-out/.update.lock` |

## Reglas

* `update` no consume tokens; `label` y `cluster-only` sin `--no-label` sí (LLM): solo a pedido explícito.
* NUNCA borres `graphify-out/` para "arreglar": se pierden `manifest.json` y `cache/`. Borrar solo `cache/` es seguro.
* NUNCA edites `graph.json` a mano ni instales `graphify hook install` / `graphify claude install`.
* NUNCA versiones `graphify-out/`. Reporta el resultado real (nodos y edges antes y después).

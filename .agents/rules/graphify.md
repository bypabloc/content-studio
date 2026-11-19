---
trigger: always_on
description: Buscar código con el grafo de graphify (query, explain, path, affected) antes de grep o lecturas a ciegas
---

# Graphify: buscar código con el grafo — SIEMPRE ACTIVA

`graphify-out/` indexa el código con AST (símbolos, imports, llamadas y comunidades de `server/src/`, `tests/` y `cli.py`). Una consulta cuesta una fracción de un grep más lectura y responde quién llama, qué rompe un cambio y por dónde pasa el flujo. Está **gitignoreado**: cada equipo lo genera con `graphify update .` (sin LLM, segundos) y los hooks lo mantienen fresco. Instalación: skill `graphify-ops`.

## 1. Orden de búsqueda

1. `graphify query "<pregunta>"` para orientarse (`--budget 400` si la respuesta es muy amplia).
2. `graphify explain "<símbolo>"`, `graphify path "A" "B"`, `graphify affected "X" --depth 2` para un símbolo, una relación o un impacto.
3. Read del `src=`/`loc=` citado.
4. Glob si el grafo no ubicó el archivo. 5. Grep como último recurso.

Los nombres del código están en español (`relaunch`, `use_venv`, `EngineSpec`, `ENGINES`): pregunta con ese vocabulario.

## 2. Excepciones: Grep directo

| Caso | Por qué |
| :--- | :--- |
| `server/data/narration/`, `server/data/music/` (datos: READMEs, catálogo, guiones), `docs/`, `server/tests/fixtures/`, `.md`, `.json`, `.toml`, logs, `tmp/`, `out/` | El grafo no los indexa o no aportan nodos |
| Literal exacto (un estilo, un flag, un mensaje) después de orientarse | El grafo indexa símbolos, no cada string |
| Grafo ausente o desactualizado | Fallback permitido; avisa que hay que correr `graphify update .` |

## 3. Frescura y procedencia

* Un `query` vacío no prueba que algo no exista: compara `git rev-parse --short HEAD` con `Built from commit` de `graphify-out/GRAPH_REPORT.md`; si difieren, `graphify update .` y repite. `--force` solo tras borrar código.
* Edges `EXTRACTED` vienen del AST y se citan directo; los `INFERRED` son hipótesis: abre el `source_location` antes de afirmarlos.

## 4. Hooks y subagentes

* `.claude/hooks/graphify_update.py` (SessionStart y PostToolBatch): si un fuente es más nuevo que `graph.json`, `graphify update .` en segundo plano con lock `graphify-out/.update.lock`.
* `.claude/hooks/graphify_guard.py` (PreToolUse de Bash, Grep, Glob y Read): sugiere el grafo al buscar o leer código; calla en las excepciones. Es una sugerencia, no un bloqueo.
* Los hooks no corren dentro de subagentes: al delegar exploración de código, repite esta regla en el prompt (`code-explorer` ya la incluye).
* **Nunca** leas `graphify-out/graph.json` con Read: se consulta por CLI. **Nunca** `graphify hook install` ni `graphify claude install`: duplicarían este cableado.

---
name: graphify-query
description: >
  Busca y explora el código de content-studio (src/, tests/, cli.py) con el grafo de graphify (query, explain, path,
  affected) en vez de grep. SIEMPRE invocar ANTES de Grep, Glob o una lectura exploratoria para ubicar o entender
  código, y NUNCA citar un archivo:línea de memoria. .agents/rules/graphify.md es la fuente. Usar cuando el usuario
  diga "busca", "dónde está", "quién llama", "qué rompe si cambio", "cómo funciona", "relación entre", "graphify",
  "grafo", "explorar el código".
allowed-tools: Read, Glob, Grep, Bash(graphify:*), Bash(git rev-parse:*)
argument-hint: "<pregunta> | path A B | explain X | affected X"
---

# Graphify query

Consulta el grafo (AST de los `.py` de `src/`, `tests/` y `cli.py`) en vez de grepear. Regla: `.agents/rules/graphify.md`.

## Flujo

1. Verifica que exista `graphify-out/graph.json`; si no, skill `graphify-ops`.
2. Elige el comando de la tabla y ejecútalo.
3. Si el resultado no sirve, reformula con el vocabulario del código, en español (`usar_venv`, `EspecMotor`, `MotorTTS`, `REGISTRO`, `relanzar`).
4. Abre con Read el `archivo:línea` citado solo para confirmar o editar. Cita siempre el `src=`/`loc=` del grafo.

| Pregunta | Comando |
| :--- | :--- |
| "cómo funciona X", "dónde está la lógica de X" | `graphify query "<pregunta>"` |
| "traza el flujo de X hasta Y" | `graphify query "<pregunta>" --dfs` |
| "qué relación hay entre A y B" | `graphify path "A" "B"` |
| "qué es X", "con qué habla X" | `graphify explain "X"` |
| "qué rompo si cambio X", "qué tests corro" | `graphify affected "X" --depth 2` |
| "panorama de la arquitectura" | Leer `graphify-out/GRAPH_REPORT.md` |

```bash
graphify query "cómo se relanza un comando en el venv de su motor" --budget 400
graphify explain "usar_venv()"
graphify affected "EspecMotor" --depth 2
```

## Reglas

* Un query vacío no prueba inexistencia: compara `git rev-parse --short HEAD` con `Built from commit` de `GRAPH_REPORT.md`.
* NUNCA leas `graphify-out/graph.json` con Read. NUNCA uses el grafo para datos (`narration/`, `music/`, `docs/`, `.md`, `.json`): ahí Grep es lo correcto.
* Distingue lo verificado (`EXTRACTED` + archivo abierto) de lo inferido (`INFERRED`).
* Al delegar exploración a un subagente, incluye en su prompt la orden de usar graphify primero.

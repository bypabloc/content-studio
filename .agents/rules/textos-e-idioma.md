---
trigger: always_on
description: Idioma del código, de los mensajes, de la documentación y de la narración (código en inglés; docs en español neutro latinoamericano, tuteo)
---

# Textos e idioma — SIEMPRE ACTIVA

content-studio no tiene catálogo i18n: sería una abstracción sin segundo uso (`plan-format.md` §0). Cada superficie tiene un idioma fijo, y lo que sí es obligatorio es la consistencia:

| Qué | Idioma y forma |
| :--- | :--- |
| Identificadores, módulos, funciones, clases y carpetas de código | Inglés: `relaunch`, `use_venv`, `EngineSpec`, `gpu_turn`, `reference/`, `voices/`. Lo que el usuario ya tiene en disco (`aprobacion.json`, el paquete `grabar/`) se mantiene hasta su spec (ver `docs/process/PENDING/`) |
| Mensajes de devtools, hooks, CI y logs | Inglés, cortos y accionables: qué falló y qué hacer (`Missing server/data/narration/engines/.venv-qwen. See the install in server/data/narration/README.md.`) |
| Ayuda de los subcomandos, flags y errores del CLI | Inglés, con los flags en inglés (`--model`, `--style`). El texto de la raíz (`cli.py`, menú y asistente) sigue en español hasta la 004 (D-3) |
| Docstrings, comentarios, README, docs, reglas y specs | Español neutro; los comandos, flags y rutas tal cual |
| Commits y PRs | Conventional Commits en español (`git-workflow.md`) |
| Prosa de `.claude/session-handoff.json` (configuración de un plugin) | Español (D-1): es instrucción para el agente, no mensaje del código |
| Narración generada | Español neutro latinoamericano, salvo que se pida otro idioma; el texto se normaliza por motor (`server/data/narration/text/`) |
| Claves de estilos, emociones y presets de música | Inglés en kebab-case (`expert`, `happy`, `lofi-rain`), definidas una sola vez en `narration/styles.py` y `music/styles.py`. Sus etiquetas en español llegan con el catálogo de la 004 |

* Un texto visible repetido en varios lugares se define una vez en su módulo (p. ej. las descripciones de motores en `registry.py`), no se copia.
* No mezcles idiomas dentro de un mismo mensaje.
* Los textos en español (docs, la raíz del CLI hasta la 004) usan tuteo neutro latinoamericano: nunca voseo ni formas peninsulares.
* El guion puede escribir sus marcas en español (`[pausa]`, `[estilo: dramatica]`, `[risa]`): el parser las convierte a su forma en inglés con los alias de `narration/script_aliases.json` (D-5).

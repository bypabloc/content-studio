# Textos e idioma — SIEMPRE ACTIVA

Todo texto visible sale de un **catálogo único con tres idiomas** (spec 007, D-1 a D-3): `server/src/content_studio/messages/{es,en,pt}.json`. El client y el server leen los mismos archivos; `es` es la base y tiene todas las claves. Fuera de la UI y la API, cada superficie tiene un idioma fijo, y lo obligatorio es la consistencia:

| Qué | Idioma y forma |
| :--- | :--- |
| Identificadores, módulos, funciones, clases y carpetas de código | Inglés: `relaunch`, `use_venv`, `EngineSpec`, `gpu_turn`, `reference/`, `voices/`. Lo que el usuario ya tiene en disco (`aprobacion.json`, el paquete `grabar/`) se mantiene hasta su spec (ver `docs/process/PENDING/`) |
| Mensajes de devtools, hooks, CI y logs | Inglés, cortos y accionables: qué falló, por qué y qué hacer; un hook que bloquea, con `Blocked by <hook>: … Why: … Instead: …`, comprobado por un test (`Missing server/data/narration/engines/.venv-qwen. See the install in server/data/narration/README.md.`) |
| Ayuda de los subcomandos, flags y errores del CLI | Inglés, con los flags en inglés (`--model`, `--style`). `studio` (`uv run studio`) va en inglés, sin menú ni asistente. Los errores de la API y de la UI están en el catálogo de tres idiomas (fila siguiente); el CLI muestra los errores de la API en español. `grabar/` (legacy) sigue en español hasta la 010 |
| Textos visibles de la UI y errores de la API | El catálogo `messages/{es,en,pt}.json`, con la misma clave en los tres idiomas. El client usa `t('clave', parámetros)` (`shared/i18n/t.ts`) y el idioma activo (`locale.ts`). La API responde en el idioma de `Accept-Language` con `error.<código>` (`messages.py`). Los nombres de idioma son «Español», «English» y «Português» |
| Docstrings, comentarios, README, docs, reglas y specs | Español neutro; los comandos, flags y rutas tal cual |
| Commits y PRs | Conventional Commits en español (`git-workflow.md`) |
| Prosa de `.claude/session-handoff.json` (configuración de un plugin) | Español (D-1): es instrucción para el agente, no mensaje del código |
| Narración generada | Español neutro latinoamericano, salvo que se pida otro idioma; el texto se normaliza por motor (`server/data/narration/text/`) |
| Claves de estilos, emociones y presets de música | Inglés en kebab-case (`expert`, `happy`, `lofi-rain`), definidas una sola vez en `narration/styles.py` y `music/styles.py`. Su nombre visible es la clave `label.<tipo>.<id>` en los tres catálogos (D-7); los `note` y `desc` de los registros quedan en inglés para el CLI |

* Un texto visible repetido en varios lugares se define una vez en su módulo (p. ej. las descripciones de motores en `registry.py`), no se copia.
* No mezcles idiomas dentro de un mismo mensaje.
* Los textos en español (docs, `messages/es.json` y `grabar/` hasta la 010) usan tuteo neutro latinoamericano: nunca voseo ni formas peninsulares.
* El guion puede escribir sus marcas en español (`[pausa]`, `[estilo: dramatica]`, `[risa]`): el parser las convierte a su forma en inglés con los alias de `narration/script_aliases.json` (D-5).

## Agregar un texto

1. La clave en inglés, con puntos y en minúsculas (`queue.announce.picked`), en **los tres** catálogos: `es.json` primero y luego `en.json` y `pt.json`, en el mismo orden alfabético. Los parámetros van entre llaves y son los mismos en los tres idiomas.
2. En el client, `t('clave', { parámetro })`; en el server, `ApiError(status, 'código')` con `error.<código>` en el catálogo, o `t('clave', idioma)`.
3. La etapa `i18n` (`python -m devtools test-runner --type=i18n`, en el pre-commit y en `all`) falla si falta una clave en un idioma, si una clave no se usa, si un parámetro no coincide, si un código de error no tiene texto, o si queda un texto visible suelto. La salida dice archivo y línea.
4. Un texto que no se muestra al usuario (un nombre técnico, una clase de Tailwind) lleva `// i18n-ignore: <motivo>` o `# i18n-ignore: <motivo>` en su línea. El motivo es obligatorio.
5. Lo que el usuario escribe (guiones, subtítulos) no pasa por el catálogo: el catálogo es solo la interfaz.

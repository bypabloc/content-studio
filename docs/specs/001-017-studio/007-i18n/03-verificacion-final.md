# 007: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Una sola vez, con todos los commits hechos y antes del push. No carga modelos: no pide turno de GPU.

## 1. Batería

1. `uv run ruff check && uv run ruff format --check`.
2. `python -m devtools test-runner --type=all` (ya incluye `i18n`), `--type=e2e` y `--type=budget`. Anota en el PR el delta del bundle (AC-9).
3. `python -m devtools test-runner --type=i18n --git-mode=all`: 0 hallazgos. Lista en el PR cada `i18n-ignore` que quedó, con su motivo.
4. `python -m devtools rules` y `python -m devtools agent-context`, más la validación headless de `agent-config-testing.md`, porque cambian reglas y `AGENTS.md`.
5. API real: `uv run studio serve --port 8765 --token T` en segundo plano, y luego `curl -s -H "Authorization: Bearer T" -H "Accept-Language: pt-BR" http://127.0.0.1:8765/jobs/nope`. Repite con `en`, `fr` y sin cabecera, y con una ruta inexistente. El `message` sale en pt, en, es, es y el de `error.http.404`. Las respuestas van en `tmp/spec-007/api-<idioma>.json`.
6. CLI sin cambios: `uv run studio --help | cat` y `uv run studio narration tts --model nope --text x | cat` siguen en inglés y no preguntan nada.

## 2. Pre-commit real (AC-6)

En el worktree, en una rama temporal `test/007-precommit` que se borra al terminar:

1. Agrega `aria-label="Cerrar"` a un `.tsx`, haz `git add` y `git commit -m "test: suelto"`. El hook lo rechaza con la línea de AC-5.
2. Agrega `return {'message': 'Listo'}` en un archivo de `api/`. El hook lo rechaza con la línea de AC-4.
3. Agrega una clave solo en `es.json`. El hook lo rechaza con la clave y los catálogos donde falta.
4. Revierte los tres cambios. Pega en el PR las salidas, guardadas en `tmp/spec-007/precommit-<caso>.log`.

## 3. App real

1. `bun run --cwd client tauri dev`: en Ajustes, cambia el idioma a English, a Português, a Español y a Sistema. La sidebar, la cola, Narración, Ajustes, los avisos y un error de la API cambian sin recargar.
2. Cierra la app y vuelve a abrirla con English: el primer cuadro ya sale en inglés.
3. Toma capturas de Ajustes y de Narración en los tres idiomas, en claro y en oscuro, en `tmp/spec-007/`. Las revisa `image-reader`: ningún texto en otro idioma, nada cortado por los textos más largos del portugués y del inglés, y la ★ en Sistema.

## 4. Cierre

* Fichas WARNING `007-catalogo-en-el-server.md`, `007-pt-br.md`, `007-detector-heuristica.md`, `007-descripciones-cli.md` y `007-cspell-pt.md`, con su fila.
* Fichas PENDING `007-revision-humana-en-pt.md` (qué la cierra: una persona revisa `en.json` y `pt.json` y se corrigen las claves que marque) y `007-plurales.md` (qué la cierra: la primera spec con un texto que depende de un número suma `_one`/`_other` con `Intl.PluralRules`).
* En `PENDING/005-avisos-sonner-ingles.md`: se quita la parte de la etiqueta de la región, o se borra la ficha si el anuncio vacío ya estaba resuelto.
* `docs/process/01-done/client.md` y `server.md`: «Qué hace hoy» (tres idiomas, selector, `Accept-Language`) y «Dónde vive» (`messages/{es,en,pt}.json`, `shared/i18n/`, la etapa `i18n`).
* El último commit hace `git rm -r docs/specs/001-017-studio/007-i18n/`, quita su fila de `docs/specs/README.md` y marca la 007 en el README del lote.

## 5. PR y merge

1. `git fetch origin dev` y merge si avanzó. Un solo push.
2. PR a `dev` si no existe, con el problema, la solución, cómo probar (los comandos de §1 y §2), el delta del budget, la lista de `i18n-ignore` y las fichas.
3. `gh pr checks <n> --watch` y, con todo verde, `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 007-i18n`.

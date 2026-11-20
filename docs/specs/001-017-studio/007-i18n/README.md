# 007: Catálogo único de textos con i18n (es, en, pt) para el client y el server

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `007-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Solo toca código, catálogos, tests, hooks y reglas. Sus pruebas escriben en `tmp/spec-007/`. Si algo parece exigir tocar datos existentes, es un `blocked — user-data`.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (unos 30 archivos: catálogos, `messages.py`, la API, `shared/i18n/` del client, Ajustes, la etapa `i18n` de devtools, el `pre-commit`, cspell y reglas) |
| Rama | `feature/007-i18n` desde `origin/dev`, en `../content-studio-worktrees/007-i18n/` |
| Depende de | 006 (fusionada en `origin/dev`) |
| Origen | Pedido del usuario (2026-11-19), lote [001-017-studio](../README.md) |

## Objetivo

Todo texto visible de content-studio (la UI del client, los errores de la API y los nombres de estilos, motores y presets) sale de **un solo catálogo por idioma**. El client y el server leen los mismos archivos, y hay tres idiomas completos: español, inglés y portugués. El idioma se elige en Ajustes («Sistema» por defecto). Una etapa nueva de `test-runner`, que corre en el `pre-commit` y en la CI, bloquea un texto suelto en el código y un catálogo incompleto. Así, de la 008 en adelante cada spec trae sus textos en los tres idiomas desde el primer commit.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md): precondición, contexto, decisiones, fuera de alcance, AC y diagrama.
* [02-plan.md](02-plan.md): ciclos TDD, archivos, tareas y commits.
* [03-verificacion-final.md](03-verificacion-final.md): batería, app real, cierre y PR.

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | Catálogo único en `server/src/content_studio/messages/`, con `en` y `pt` | PEN |
| 2 | Etapa `i18n`: catálogos parejos, claves en uso y mapeos de estilos y motores | PEN |
| 3 | Server: `t(code, locale)` y negociación de `Accept-Language` | PEN |
| 4 | Client: idioma activo, `t()` con locale, selector en Ajustes | PEN |
| 5 | Detector de textos sueltos (Python y TS) en el `pre-commit` y en `all`, y reglas | PEN |

## Decisiones clave

* D-1: el catálogo vive en `server/src/content_studio/messages/{es,en,pt}.json`. El server lo lee en tiempo de ejecución y el client lo importa al compilar (alias `@messages`). Son los mismos archivos, sin copias ni sincronización.
* D-2: JSON plano, con claves en inglés separadas por puntos y en orden alfabético, y parámetros `{nombre}`. `es.json` es la base y de ahí sale el tipo `MessageKey`. Los errores de la API van en `error.<code>` y las etiquetas en `label.*`.
* D-3: `es` (español neutro latinoamericano), `en` (inglés de EE. UU.) y `pt` (portugués de Brasil). Los tres tienen las mismas claves y los mismos parámetros: la etapa `i18n` falla si no.
* D-4: el server responde en el idioma de `Accept-Language` (lo manda el client). Sin cabecera o con un idioma no soportado, responde en español.
* D-5: el client tiene el idioma activo en `shared/i18n/` y cambia sin recargar; `<html lang>` lo sigue. La preferencia `ui.language` (`system`, `es`, `en` o `pt`) queda en caché local, igual que el tema.
* D-6: la etapa `i18n` de `test-runner` revisa los catálogos, las claves en uso, los mapeos y los **textos sueltos**: con `ast` en Python y con la API de TypeScript en el client. Corre en el `pre-commit` sobre lo staged y en `all`.

## WARNING y PENDING

* WARNING: `007-catalogo-en-el-server.md` (D-1), `007-pt-br.md` (D-3), `007-detector-heuristica.md` (D-6: qué cuenta como texto y qué no), `007-descripciones-cli.md` (D-7: el CLI conserva sus descripciones en inglés en los registros), `007-cspell-pt.md` (D-9).
* PENDING: `007-revision-humana-en-pt.md` (traducciones del agente para que las revise una persona), `007-plurales.md` (sin plurales hasta que un texto los pida).

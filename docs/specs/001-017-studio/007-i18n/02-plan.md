# 007: plan

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`.

Tests en las rutas espejo (`server/tests/unit/src/…`, `client/tests/unit/src/…`, `devtools/tests/unit/…`), con cobertura ≥ 80 % por archivo. Nada carga un modelo: la spec no pide turno de GPU.

## 1. Ciclos TDD

#### Ciclo 1: catálogo único en el paquete del server [AC-2, AC-7 parcial]

- **RED**:
  - `server/tests/unit/src/content_studio/test_messages.py::test_t_reads_the_locale_catalog`: `t('error.unknown_engine', 'en', model='x')` devuelve el texto inglés con `x`.
  - `client/tests/unit/src/shared/i18n/t.test.ts`: `t('nav.settings')` sale del catálogo importado con `@messages/es.json`.
  - Fallan porque no existen ni `en.json` ni el alias.
- **GREEN**:
  - Fusionar `client/messages/es.json` en `server/src/content_studio/messages/es.json`.
  - Renombrar los códigos de la API a `error.<code>` y ordenar las claves.
  - Escribir `en.json` y `pt.json` completos (D-3).
  - `messages.py` con `t(code, locale='es', **params)` y `_http_error` con `error.<code>` (por ahora siempre en `es`).
  - En el client: el alias `@messages` en `vite.config.ts`, `tsconfig.app.json` y `vitest.config.ts`, y `server.fs.allow`. `t.ts` importa de `@messages`.
  - Borrar `client/messages/` y actualizar la ruta del catálogo en `catalog-keys.test.ts`, que el ciclo 3 reemplaza.
  - Verify: `uv run pytest server/tests/unit/src/content_studio/test_messages.py -q` y `bun run --cwd client test -- shared/i18n`.
- **REFACTOR**: ninguno.

#### Ciclo 2: etapa `i18n`, catálogos parejos [AC-1]

- **RED**: `devtools/tests/unit/test_runner/test_i18n.py::test_ac1_*`. Una fixture por defecto en `devtools/tests/fixtures/i18n/catalogs/<caso>/`: clave faltante, parámetro distinto, desorden, clave repetida y valor vacío. Más un caso válido.
- **GREEN**:
  - `devtools/test_runner/i18n.py` con `check_catalogs(dir) -> list[str]`.
  - La línea en `STAGES` y `FILE_STAGES`, y `tests/validators/i18n.json` (rutas, `dynamicPrefixes`, `allowed`, `python.include`).
  - Verify: `uv run pytest devtools/tests/unit/test_runner/test_i18n.py -q` y `python -m devtools test-runner --type=i18n`.
- **REFACTOR**: ninguno.

#### Ciclo 3: claves en uso y mapeos [AC-3]

- **RED**:
  - `test_i18n.py::test_ac3_*` con fixtures: `t('missing.key')` en un `.tsx`, una clave huérfana, `ApiError(404, 'sin_texto')` en un `.py` y un prefijo dinámico sin claves.
  - `test_messages.py::test_ac3_every_registry_id_has_a_label`.
- **GREEN**:
  - `check_usage(...)` en la etapa: las claves del client con la regex de `t('…')` sobre el texto, porque la etapa es stdlib; el análisis completo de TS es del ciclo 7. Los códigos del server, con `ast`.
  - Las claves `label.*` de cada id de los registros, en los tres catálogos.
  - Borrar `client/tests/unit/src/shared/i18n/catalog-keys.test.ts`.
  - Verify: los dos tests y `--type=i18n`.
- **REFACTOR**: si `i18n.py` pasa de 300 líneas, dividirlo en `i18n_catalogs.py`, `i18n_usage.py` e `i18n_loose.py`.

#### Ciclo 4: idioma de la API [AC-2]

- **RED**:
  - `test_messages.py::test_negotiate_*`: `pt-BR,pt;q=0.9` → `pt`; `en;q=0.1, pt;q=0.5` → `pt`; `fr-FR` → `es`; vacío → `es`; cabecera mal formada → `es`.
  - `server/tests/unit/src/content_studio/api/test_errors_locale.py`: `GET /jobs/nope` con las tres cabeceras y una ruta inexistente (`code: 'http.404'`).
- **GREEN**:
  - `messages.negotiate(header)`.
  - `_http_error` lee `request.headers.get('accept-language')`, y el `HTTPException` sin código pasa a `http.<status>`.
  - Claves `error.http.{404,405,422,500}`.
  - Verify: `uv run pytest server/tests/unit/src/content_studio/api server/tests/unit/src/content_studio/test_messages.py -q`.
- **REFACTOR**: ninguno.

#### Ciclo 5: idioma activo del client [AC-7]

- **RED**:
  - `client/tests/unit/src/shared/i18n/locale.test.ts`: `resolveLocale`, `setLocale` y `subscribe`, `<html lang>` y la caché `ui.language`.
  - `t.test.ts`: el idioma activo, el respaldo a `es` y a la clave, y los parámetros.
  - `shared/api/client.test.ts`: la cabecera `Accept-Language`.
  - `shared/api/errors.test.ts`: el `ApiError` traducido desde su código.
- **GREEN**:
  - `shared/i18n/catalogs.ts`, `locale.ts` (con `useLocale`) y `t.ts`.
  - La cabecera en `client.ts` y `errors.ts`.
  - En `App.tsx`, `key={locale}` en la raíz para volver a renderizar.
  - Verify: `bun run --cwd client test -- shared`.
- **REFACTOR**: si la caché del tema y la del idioma repiten código, sacar `readCached(key, values, fallback)` a `shared/settings/cache.ts`. Es el segundo uso real.

#### Ciclo 6: selector en Ajustes y avisos [AC-8]

- **RED**:
  - `client/tests/unit/src/features/settings/SettingsPage.test.tsx`: «Idioma» con cuatro opciones y la ★ en Sistema. Al elegir «English», la página cambia de idioma y se guarda `ui.language`. «Restablecer elecciones» no lo toca.
  - `tests/e2e/settings/happy-language.e2e.ts`: cambiar a English y a Português, recorrer la sidebar, la cola y Narración, recargar (persiste) y correr axe en los dos.
- **GREEN**:
  - `SettingsPage.tsx`, con las claves `settings.language` y `language.*`.
  - `containerAriaLabel={t('notify.region')}` en el `Toaster` de `Shell.tsx`.
  - Verify: `bun run --cwd client test -- settings` y `python -m devtools test-runner --type=e2e`.
- **REFACTOR**: ninguno.

#### Ciclo 7: textos sueltos en Python y TS [AC-4, AC-5]

- **RED**:
  - `test_i18n.py::test_ac4_*`: fixtures `.py` en `devtools/tests/fixtures/i18n/server/`, con los casos que fallan y los que no de AC-4.
  - `test_i18n.py::test_ac5_*`: fixtures `.tsx` en `devtools/tests/fixtures/i18n/client/`, con los de AC-5.
  - Más la regla de qué cuenta como texto (D-8) como tabla de casos: `'Cancelar'` sí, `'cancel'` no, `'Ctrl+K'` no, `'ApiError'` no, `'año'` sí, `'¿Borrar?'` sí, `'lofi-chill'` no.
- **GREEN**:
  - `check_loose_python(files)` con `ast` en la etapa.
  - `client/scripts/loose-texts.ts`, con la API de `typescript`: recibe rutas y devuelve JSON con los hallazgos. La etapa lo corre con `bun run --cwd client`, como las etapas `client-*` de `client.py`. Si falta `bun` o `node_modules`, sale con exit 2 y un mensaje accionable.
  - Correr la etapa sobre todo el repo y pasar cada hallazgo a `t()`/`ApiError`, o marcarlo con `i18n-ignore: <motivo>` si no es texto visible.
  - Verify: `uv run pytest devtools/tests/unit/test_runner/test_i18n.py -q` y `python -m devtools test-runner --type=i18n --git-mode=all` con 0 hallazgos.
- **REFACTOR**: la regla de «qué cuenta como texto» vive una sola vez por lenguaje: en `i18n.py` y en `loose-texts.ts`. Los dos se prueban con la misma tabla, `devtools/tests/fixtures/i18n/prose-cases.json`.

#### Ciclo 8: pre-commit, `all`, cspell y reglas [AC-6, AC-9, AC-10]

- **RED**:
  - `test_i18n.py::test_ac6_precommit_runs_i18n`: el `test-runner` del `pre-commit` incluye `i18n` y `GROUPS['all']` también.
  - Una fixture `en.json` con una palabra mal escrita para `--type=spelling`.
- **GREEN**:
  - `.git-hooks/pre-commit`: `--type=lint,spelling,validators,i18n`.
  - `i18n` en `GROUPS['all']`.
  - En `cspell.config.yaml`: los overrides de `en`, `es` y `pt` y el import de `@cspell/dict-pt-br` (`bun add -d --exact` en la raíz).
  - Reescribir `textos-e-idioma.md`, `frontend-stack.md` y `ui-components.md` en `.agents/`, y la línea de `AGENTS.md`. Después `python -m devtools rules --sync`.
  - Verify: `python -m devtools test-runner --type=all`, `python -m devtools rules` y `python -m devtools agent-context`.
- **REFACTOR**: ninguno.

## 2. Archivos

| Acción | Archivo | Verify |
| :--- | :--- | :--- |
| Crear | `server/src/content_studio/messages/{en,pt}.json` | `--type=i18n` |
| Modificar | `server/src/content_studio/messages/es.json` (fusión, `error.*`, `label.*`, `language.*`), `messages.py`, `api/app.py` | `uv run pytest server/tests/unit/src/content_studio -q` |
| Borrar | `client/messages/es.json`, `client/tests/unit/src/shared/i18n/catalog-keys.test.ts` | `--type=i18n` (lo reemplaza) |
| Crear | `client/src/shared/i18n/{catalogs,locale}.ts`, `client/scripts/loose-texts.ts` | `client-unit`, `test_i18n.py` |
| Modificar | `client/src/shared/i18n/t.ts`, `shared/api/{client,errors}.ts`, `app/{App,Shell}.tsx`, `features/settings/SettingsPage.tsx`, `shared/theme/theme.ts` (si sale `cache.ts`), `vite.config.ts`, `tsconfig.app.json`, `vitest.config.ts` | `client-unit`, `client-typecheck` |
| Modificar | Los archivos de `client/src/` y del server que la etapa marque al pasar sus textos a `t()` (ciclo 7) | `--type=i18n --git-mode=all` |
| Crear | `devtools/test_runner/i18n.py` (o los tres de la división del ciclo 3), `tests/validators/i18n.json`, `devtools/tests/unit/test_runner/test_i18n.py`, `devtools/tests/fixtures/i18n/**` | `uv run pytest devtools/tests/unit/test_runner/test_i18n.py -q` |
| Modificar | `devtools/test_runner/main.py`, `.git-hooks/pre-commit`, `cspell.config.yaml`, `package.json`, `bun.lock` | `--type=all` |
| Crear | `server/tests/unit/src/content_studio/api/test_errors_locale.py`, `client/tests/unit/src/shared/i18n/locale.test.ts`, `client/tests/unit/src/features/settings/SettingsPage.test.tsx` (si no existe), `tests/e2e/settings/happy-language.e2e.ts` | ídem |
| Modificar | `.agents/rules/{textos-e-idioma,frontend-stack,ui-components}.md`, sus copias en `.claude/rules/`, `AGENTS.md` | `python -m devtools rules` y `agent-context` |

Cada `.py` queda en 300 líneas o menos, y cada test, en 800 (`codigo-python.md`).

## 3. Tareas

| Tarea | Archivos | AC | Depende de | Verify | Done |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | Catálogo único y alias (ciclo 1) | AC-2, AC-7 | — | pytest de `messages` y `client-unit` | [ ] |
| T2 | Traducciones `en` y `pt` (ciclo 1) | AC-1 | T1 | `--type=i18n` | [ ] |
| T3 | Etapa `i18n`: catálogos (ciclo 2) | AC-1 | T1 | `test_i18n.py` | [ ] |
| T4 | Claves en uso y mapeos (ciclo 3) | AC-3 | T3 | `test_i18n.py`, `test_messages.py` | [ ] |
| T5 | Negociación de idioma en la API (ciclo 4) | AC-2 | T1 | pytest de `api` | [ ] |
| T6 | Idioma activo del client (ciclo 5) | AC-7 | T1 | `client-unit` | [ ] |
| T7 | Selector en Ajustes y sonner (ciclo 6) | AC-8 | T6 | `client-unit`, `e2e` | [ ] |
| T8 | Detector de textos sueltos y limpieza del repo (ciclo 7) | AC-4, AC-5 | T3 | `--type=i18n --git-mode=all` | [ ] |
| T9 | Pre-commit, `all`, cspell y reglas (ciclo 8) | AC-6, AC-9, AC-10 | T8 | `--type=all`, `rules`, `agent-context` | [ ] |

## 4. Commits

En Conventional Commits en español, en orden. Cada uno deja verdes `uv run ruff check`, `uv run ruff format --check`, `uv run pytest` y `client-unit`.

1. `refactor: catálogo único de textos en el paquete del server, usado por el client` (T1).
2. `feat: catálogos en inglés y portugués` (T2).
3. `feat: etapa i18n de test-runner que valida los catálogos` (T3).
4. `feat: la etapa i18n comprueba claves en uso, códigos de la API y etiquetas de los registros` (T4).
5. `feat: la API responde en el idioma de Accept-Language` (T5).
6. `feat: idioma activo en el client con t() por locale` (T6).
7. `feat: selector de idioma en Ajustes` (T7).
8. `feat: la etapa i18n bloquea textos sueltos en Python y TS` (T8; incluye los textos movidos al catálogo).
9. `chore: etapa i18n en el pre-commit y en all, cspell en y pt` (T9, código).
10. `docs: reglas de textos con el catálogo único y la etapa i18n` (T9, reglas).
11. `docs: cierre de la 007` (fichas WARNING y PENDING, `01-done/` y `git rm -r` de esta carpeta, con su fila en los dos índices).

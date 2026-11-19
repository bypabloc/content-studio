# 002: código y datos en inglés, validados con el cspell de klinikae

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `002-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en `out/<herramienta>/spec-002/` o `tmp/spec-002/`. **Excepción pedida por el usuario**: `move-data` **renombra** (nunca copia ni borra) carpetas y archivos de datos a inglés (§D-4 de `01`).

| Campo | Valor |
| :--- | :--- |
| Tipo | refactor |
| Escala | Large (unos 70 `.py`, datos, reglas y docs) |
| Rama | `refactor/002-english-cspell` desde `origin/dev`, en `../content-studio-worktrees/002-english-cspell/` |
| Depende de | [001](../001-server-devtools/README.md) (fusionada en `origin/dev`) |
| Origen | Pedido del usuario (lote [001-017-studio](../README.md)) |

## Objetivo

Que nada del código esté en español. Identificadores, módulos, flags, claves de datos, strings, logs y nombres de tests van en inglés, y el español queda solo en docstrings, comentarios, `.md` y catálogos. Lo hace cumplir el `cspell.config.yaml` traído de klinikae, que corre en el pre-commit y en la CI.

## Índice

* [01-contexto-y-decision.md](01-contexto-y-decision.md)
* [02-plan.md](02-plan.md)
* [03-verificacion-final.md](03-verificacion-final.md)

## Fases

| Fase | Qué | Estado |
| :--- | :--- | :--- |
| 1 | bun en la raíz, cspell, `devtools spelling` y los gates | PEN |
| 2 | Migración de datos a nombres en inglés (`move-data`, segundo paso) | PEN |
| 3 | Traducción del código por paquete: common, narration, music, devtools, hooks y tests | PEN |
| 4 | Flags en inglés, alias del guion, reglas y README | PEN |

## Decisiones clave

* D-1: `cspell.config.yaml` adaptado de klinikae, con el diccionario propio en `devtools/cspell/content-studio-terms.txt`.
* D-2: bun en la raíz (`package.json` con workspaces). cspell y `@cspell/dict-es-es` como devDependencies.
* D-3: `cli/` (salvo `comandos/`) y `narration/grabar/` quedan excluidos de forma temporal (PENDING, se cierra con la 004 y la 007).
* D-4: `move-data` pasa a ser una lista ordenada de migraciones y suma el renombrado de los datos a inglés.
* D-5: el guion canónico usa `[pause N]` y `"text"`, y acepta `[pausa N]` y `"texto"` como alias.
* D-6: los flags del CLI van en inglés, y se actualizan las reglas y los README.

## WARNING y PENDING

* WARNING: `002-mapeo-de-nombres.md` (tabla de nombres viejos y nuevos de estilos, emociones, carpetas y flags).
* PENDING: `002-cspell-excepciones-temporales.md` (cli/ y grabar/; la cierran la 004 y la 007).

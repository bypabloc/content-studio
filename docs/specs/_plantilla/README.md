# Spec <NN>: <título en una línea>

<!--
Plantilla de spec de content-studio (regla plan-format.md). Cómo usarla:

1. Copia la carpeta: `cp -r docs/specs/_plantilla docs/specs/<NN>-<slug>` (en un lote,
   `docs/specs/<lote>/<NN>-<slug>`). El número es el siguiente libre de docs/specs/README.md.
2. Escala: Micro (1-2 archivos de código) deja solo este README, con contexto, AC, ciclos,
   archivos, commit y verificación condensados; borra el resto. Small (3-5) deja 01, una
   fase y 03; 02-diseno.md es opcional. Medium y Large usan todo. Más de 8 ciclos TDD o
   más de 5 fases: se divide en un lote.
3. Una fase = un grupo de commit = una carpeta `fases/<n>-<tema>/` con plan-tdd.md,
   archivos.md y commits.md. Copia `fases/1-tema/` por cada fase y renómbrala (`fases/2-<tema>/`…).
4. Reemplaza todo lo que esté entre <...> y borra estos comentarios. Una sección que no
   aporta se borra o dice «no aplica».
5. En un lote, las rutas a docs/process/ del bloque fijo suben un nivel más (`../`).
-->

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../process/WARNING/README.md) (ficha `<NN>-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-<NN>/` o `tmp/spec-<NN>/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature · fix · refactor · perf · experiment · docs · chore |
| Escala | Micro (1–2 archivos) · Small (3–5) · Medium (6–10) · Large (11+) |
| Rama | `<prefijo>/<NN>-<slug>` desde `origin/dev`, en `../content-studio-worktrees/<NN>-<slug>/` |
| Depende de | `<spec>` (comprobada en la Precondición de 01) · ninguna |
| Origen | Pedido del usuario · `docs/process/02-next/<NN>-<slug>.md` · `docs/research/<tema>/` |

## Objetivo

<Una o dos oraciones: qué cambia para el usuario y por qué.>

## Cuándo leer cada archivo

| Archivo | Qué trae | Cuándo leer |
| :--- | :--- | :--- |
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Precondición, términos, hallazgos, decisiones D-n, fuera de alcance, AC, debe sonar | Primero |
| [02-diseno.md](02-diseno.md) | Flujo antes/después, CLI y API, datos, diseño por módulo, textos | Antes de la primera fase |
| [fases/1-tema/](fases/1-tema/plan-tdd.md) | Ciclos TDD, archivos y commit de la fase 1 | Al implementar la fase 1 |
| [03-verificacion-final.md](03-verificacion-final.md) | Batería, mediciones, escucha, cierre y PR | Con todos los commits hechos |

## Estado por fase

Estados: `PEN` (pendiente) o `IMP` (implementada, con su commit). El estado va en la última columna.

| Fase | Qué | Ciclos | AC | Commit | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F1 | [<tema>](fases/1-tema/plan-tdd.md) | C1, C2 | AC-1 | - | PEN |
| FV | [Verificación final](03-verificacion-final.md) | - | todos | - | PEN |

## Decisiones cerradas (no reabrir)

Una línea por decisión; el motivo y la alternativa descartada van en [01 §3](01-contexto-y-decision.md#3-solución).

1. **D-1**: <decisión> (<quién y cuándo>).

## Reglas críticas

<Restricciones de esta spec que quien implemente no puede saltarse. Parte de estas y borra las que no apliquen:>

- Solo lo que piden los AC; nada de «Fuera de alcance».
- Dos capas: torch, numpy y las librerías de motor se importan dentro de funciones (`codigo-python.md`).
- Cada `.py` de fuente en 300 líneas o menos; tests en 800.
- Textos visibles en los tres catálogos `messages/{es,en,pt}.json`; identificadores en inglés.
- Lo que carga un modelo, con el turno de la GPU (`turno-gpu.md`); la música es siempre instrumental.

## Matriz de verificación

Todo AC tiene al menos un test. Se completa al redactar y se marca al implementar.

| AC | Fase | Ciclo | Test | Verificación real |
| :--- | :--- | :--- | :--- | :--- |
| AC-1 | F1 | C1 | `server/tests/<ruta>::test_ac1_<caso>` | <corrida real y medición, e2e o «solo pytest»> |

## WARNING y PENDING

- WARNING: <fichas que deja o «ninguna»>.
- PENDING: <fichas que deja o «ninguna»>.

# Formato de spec (plan de implementación) — SIEMPRE ACTIVA

Todo plan formal es una carpeta en `docs/specs/` y sigue **Explore → Interview → Plan → Implement (TDD) → Commit**. Las plantillas, con el texto fijo de cada archivo, están en [`docs/specs/_plantilla/`](../../docs/specs/_plantilla/README.md): **cópialas, no las reescribas**. Skills: `crear-spec` para redactar, `execute-spec` para implementar, `run-specs` para varias. Traído de klinikae.

## 0. Principio rector: K.I.S.S.

* La solución más simple que cumple los AC. Escalera, en orden: ¿debe existir? ¿ya existe en el repo (`graphify query`)? ¿la resuelve la stdlib o una dependencia que ya está? Solo si las tres son no, se diseña algo nuevo, y la spec dice por qué.
* Prohibido sin una razón escrita en la decisión: una abstracción antes del tercer uso real (y Factory Method solo con dos o más productos, `codigo-python.md`), flags o configuración para casos que ningún AC pide, un módulo nuevo cuando basta una función, una dependencia nueva, generalizar «por si acaso».
* **Fuera de alcance** es obligatorio en `01`; lo pendiente va a `docs/process/02-next/` o `PENDING/`, no a la spec.

## 1. Cuándo y cómo

* Se aplica al diseñar un motor nuevo, un comando, un refactor mayor o un fix no trivial, o cuando el usuario pide «plan», «diseñar», «spec», «desglosar».
* **Explore**: lee el código y las reglas del área antes de preguntar. **Interview**: 1–4 preguntas por ronda con opciones concretas; no preguntes lo que el código responde. La spec final no lleva `TODO` ni «por confirmar».
* **Una spec = una rama desde `origin/dev` en su worktree (`worktrees.md`) = un PR a `dev`**. Las fases son etapas internas, no PRs.
* Numeración: `<NN>-<slug>`, con `NN` el siguiente libre del índice [`docs/specs/README.md`](../../docs/specs/README.md); la rama es `<prefijo>/<NN>-<slug>`.

## 2. Carpeta y escala

Toda spec nueva se copia de la plantilla (`cp -r docs/specs/_plantilla docs/specs/<NN>-<slug>`); no se inventa otra estructura. Al terminar no quedan marcadores `<...>` ni comentarios de la plantilla. Si cambia la estructura, se cambian la plantilla y esta regla en el mismo PR.

```text
docs/specs/<NN>-<slug>/
├── README.md                  # índice, metadatos, estado por fase, decisiones cerradas, reglas críticas, matriz AC → fase → ciclo → test
├── 01-contexto-y-decision.md  # precondición, términos, hallazgos con evidencia, D-n, fuera de alcance, AC, «debe sonar»
├── 02-diseno.md               # transversal: flujo antes/después, CLI y API, datos, diseño por módulo, textos
├── fases/<n>-<tema>/          # una fase = un grupo de commit
│   ├── plan-tdd.md            # ciclos TDD y matriz e2e de la fase
│   ├── archivos.md            # crear/modificar/eliminar con Verify
│   └── commits.md             # mensaje exacto y gate del grupo
└── 03-verificacion-final.md   # batería, mediciones y escucha, cierre y PR
```

| Escala | Archivos de código | Carpeta |
| :--- | :--- | :--- |
| Micro | 1–2 | Solo `README.md`, con contexto, AC, ciclos, archivos, commit y verificación condensados |
| Small | 3–5 | README, `01`, una fase y `03` (`02` opcional) |
| Medium / Large | 6+ | La plantilla completa; más de 8 ciclos TDD o 5 fases se divide en un lote |

* **Fase = grupo de commit**: cada carpeta de `fases/` deja verdes ruff y pytest y termina en un commit; su fila de «Estado por fase» del README pasa a `IMP` con el hash. Lo propio de una fase va en su `plan-tdd.md`; `02-diseno.md` solo trae lo que comparten varias.
* El bloque fijo de **decisiones** (se toman sin preguntar y van a `docs/process/WARNING/`) y de **datos del usuario** (la spec no borra ni cambia voces grabadas, `out/` ni modelos que no creó) va en los archivos raíz y en cada `plan-tdd.md`, con las rutas relativas un nivel más arriba por carpeta. Texto exacto en la plantilla.
* `_plantilla/` es permanente y no lleva fila en el índice.
* **Lote**: dos o más specs de un mismo pedido en `docs/specs/<primera>-<última>-<tema>/`, cada una con la plantilla; la última es la de verificación integral (escucha comparada, todas las salidas juntas) y borra la carpeta del lote.

## 3. Contenido

* **AC** en BDD (`Given/When/Then`) o EARS (`WHEN … THEN …`), `AC-1`…, cada uno verificable con una prueba (pytest, doctest o una medición de la salida real: duración, volumen, espectrograma). Ciclos (`C1`…) y AC con numeración global a la spec; la matriz del README cruza AC → fase → ciclo → test.
* **Hallazgos** de `01` con evidencia (archivo y símbolo del grafo, o una medición con fecha); cada `D-n` con la alternativa descartada y repetida en una línea en «Decisiones cerradas» del README.
* **Ciclo TDD**: RED (test en `server/tests/test_<área>.py` o doctest, con el AC en el nombre o el docstring; falla por el motivo esperado), GREEN (mínimo, con su Verify), REFACTOR. Un fix empieza con un test de regresión en `server/tests/test_bugs.py`.
* Si la spec toca la salida de audio: «debe sonar / no debe sonar» en `01` (duración, volumen LUFS, sin voz en la música, sin cortes) y la escucha la hace el usuario al final: si hay que elegir entre opciones, el agente elige con ese criterio, lo registra en `docs/process/WARNING/` y sigue.

## 4. Por grupo de commit y verificación final

* Por fase: el Verify de sus archivos, `uv run ruff check`, `uv run ruff format --check` y `uv run pytest`. Nada que cargue un modelo por grupo.
* **Verificación final**, una vez, con todos los commits hechos y antes del push: lo anterior, `uv run pytest -m local` si toca un motor, la corrida real con `gpu-turn run` de lo que cambió, y duración, volumen y espectrograma de las salidas (`verify-before-claiming-done.md`; las imágenes las abre `image-reader`).
* Lo que bloquea el pase a `main` va a `docs/process/WARNING/`; lo que no, a `docs/process/PENDING/` (`project-progress.md`). Nada importante puede quedar solo en la carpeta de la spec: se borra al cerrar.
* Un solo push y un solo PR a `dev`, creado solo si no existe; merge con merge commit y cierre del worktree.
* **Cierre**: el último commit de una spec suelta actualiza `docs/process/01-done/` si es funcional, hace `git rm -r` de su carpeta y quita su fila del índice.

## 5. Dependencias

Una spec que depende de otra lo declara en su README y lo comprueba contra `origin/dev` antes del primer commit; si falla, primero se fusiona la dependencia. Si la dependencia cambió algo que la spec cita, una fase `0-ajustes` ajusta la carpeta en un commit `docs:` antes de seguir.

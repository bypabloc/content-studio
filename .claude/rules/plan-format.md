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

```text
docs/specs/<NN>-<slug>/
├── README.md                  # tipo, escala, rama, dependencias, objetivo, fases (PEN/IMP), WARNING/PENDING
├── 01-contexto-y-decision.md  # precondición, contexto, decisiones D-n, fuera de alcance, AC, diagrama, «debe sonar»
├── 02-plan.md                 # ciclos TDD, archivos, tareas y commits
└── 03-verificacion-final.md   # batería, escucha y espectrograma, cierre y PR
```

| Escala | Archivos de código | Carpeta |
| :--- | :--- | :--- |
| Micro | 1–2 | Solo `README.md`, con todo condensado y un commit |
| Small / Medium | 3–10 | Los cuatro archivos |
| Large | 11+ | Si pasa de 8 ciclos TDD, se divide en un lote |

* Cada archivo abre con el bloque fijo de **decisiones** (se toman sin preguntar y van a `docs/process/WARNING/`) y de **datos del usuario** (la spec no borra ni cambia voces grabadas, `out/` ni modelos que no creó). Texto exacto en la plantilla.
* **Lote**: dos o más specs de un mismo pedido en `docs/specs/<primera>-<última>-<tema>/`; la última es la de verificación integral (escucha comparada, todas las salidas juntas) y borra la carpeta del lote.

## 3. Contenido

* **AC** en BDD (`Given/When/Then`) o EARS (`WHEN … THEN …`), `AC-1`…, cada uno verificable con una prueba (pytest, doctest o una medición de la salida real: duración, volumen, espectrograma).
* **Ciclo TDD**: RED (test en `tests/test_<área>.py` o doctest, con el AC en el nombre o el docstring; falla por el motivo esperado), GREEN (mínimo, con su Verify), REFACTOR. Un fix empieza con un test de regresión en `tests/test_bugs.py`.
* Si la spec toca la salida de audio: «debe sonar / no debe sonar» en `01` (duración, volumen LUFS, sin voz en la música, sin cortes) y la escucha la decide el usuario (`blocked — taste` solo si hay que elegir entre opciones).

## 4. Por grupo de commit y verificación final

* Por grupo: el Verify de sus tareas, `uv run ruff check`, `uv run ruff format --check` y `uv run pytest`. Nada que cargue un modelo por grupo.
* **Verificación final**, una vez, con todos los commits hechos y antes del push: lo anterior, `uv run pytest -m local` si toca un motor, la corrida real con `turno-gpu run` de lo que cambió, y duración, volumen y espectrograma de las salidas (`verify-before-claiming-done.md`; las imágenes las abre `image-reader`).
* Lo que bloquea el pase a `main` va a `docs/process/WARNING/`; lo que no, a `docs/process/PENDING/` (`project-progress.md`). Nada importante puede quedar solo en la carpeta de la spec: se borra al cerrar.
* Un solo push y un solo PR a `dev`, creado solo si no existe; merge con merge commit y cierre del worktree.
* **Cierre**: el último commit de una spec suelta actualiza `docs/process/01-done/` si es funcional, hace `git rm -r` de su carpeta y quita su fila del índice.

## 5. Dependencias

Una spec que depende de otra lo declara en su README y lo comprueba contra `origin/dev` antes del primer commit; si falla, primero se fusiona la dependencia.

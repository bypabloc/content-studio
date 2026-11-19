# 018: verificación final

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación. Cada una queda en [`docs/process/WARNING/`](../../../process/WARNING/README.md); toda revisión pendiente, en [`docs/process/PENDING/`](../../../process/PENDING/README.md).
>
> **Datos del usuario: solo los que crea esta spec**. No borra ni sobrescribe voces grabadas, voces construidas, salidas de `out/` ni modelos que no creó; si algo parece exigirlo, es un `blocked — user-data`. La Biblioteca nunca borra nada sola.

## 1. Batería

1. `python -m devtools test-runner --type=all`, `--type=e2e`, `--type=budget` y `--type=guard-tdd`.
2. `uv run pytest -m local` (papelera real sobre un archivo de `tmp/spec-018/`).
3. `uv run studio library list --kind music | cat` y `uv run studio library trash <ruta dentro de reference/>`, que tiene que salir con exit 1 y `protected_path`.

## 2. Corridas reales

1. Abre la Biblioteca en el principal (con las salidas reales de las specs anteriores): aparecen todas, con miniaturas, duración y origen.
2. Agrega como carpeta vigilada una de prueba en `tmp/spec-018/videos/` con 3 medios copiados (datos de la spec). Escanea, borra uno desde el explorador y escanea otra vez: queda marcado como faltante.
3. Busca un texto que está en un guion de la 006 con «Buscar en el contenido». Etiqueta y agrega a un proyecto. Filtra.
4. «Editar y repetir» sobre una música, y «Mandar a Limpiador» sobre un video.
5. Renombra un archivo de prueba y comprueba el disco y `GET /library/{id}`. Muévelo a otra carpeta de prueba.
6. «Tomas no elegidas»: manda a la papelera **solo las tomas creadas por las specs de prueba** (las de `spec-0NN`), y comprueba que están en la papelera de Windows y se pueden restaurar. Ninguna salida que no sea de prueba se toca sin que el usuario lo pida.
7. Espacio: las sumas coinciden con `du -sb` de `outputs_dir()` (± lo que no está indexado, que se anota).
8. Capturas de la grilla, la lista, el detalle y Espacio en claro y en oscuro en `tmp/spec-018/`, que revisa `image-reader`.

## 3. Cierre

* `docs/process/01-done/library.md`, nueva.
* Fichas WARNING `018-send2trash.md` y `018-busqueda-en-disco.md`.
* Se borra `tmp/spec-018/` (datos de la spec).
* Estado de la fila 018 en el README del lote.

## 4. PR y merge

1. `git fetch origin dev` y merge si avanzó; un solo push.
2. PR a `dev` si no existe, con las capturas y las fichas.
3. `gh pr checks <n> --watch` y `gh pr merge <n> --merge`.
4. En el principal: `git switch dev && git pull` y `python -m devtools worktree close 018-library`.

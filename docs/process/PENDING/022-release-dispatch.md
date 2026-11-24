# 022: correr release.yml en dry-run en GitHub

- **Qué**: AC-10 se probó en local (`version --check --expect` falla con otro tag y el build con un segundo `--config` compila sin firma). `workflow_dispatch` solo se puede lanzar cuando el workflow está en la rama por defecto (`main`).
- **Por qué no se hizo**: el lote no pasa a `main` sin el pedido del usuario.
- **Cuándo**: al pasar el lote a `main`, antes del primer tag.
- **Quién**: agente.
- **Qué la cierra**: `gh workflow run release.yml -f tag=v9.9.9 -f dry-run=true` falla en el primer paso y `-f tag=v0.1.0` sube el instalador como artefacto.

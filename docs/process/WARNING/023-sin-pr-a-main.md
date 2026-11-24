# 023: el PR dev → main queda listo, sin abrirse

- **Contexto**: la spec 023 (D-3) pide abrir el PR `dev → main` sin fusionarlo. `git-workflow.md` dice que no se abre ni un PR a `main` hasta que el usuario lo pida, y que cerrar un lote no lo autoriza.
- **Elegida**: seguir la regla: la 023 se fusiona en `dev` y el informe con el título, el cuerpo y los pasos para publicar queda en el PR de la 023 para cuando el usuario lo pida.
- **Descartadas**: abrir el PR a `main` (contradice la regla vigente).
- **Cómo revertir**: `gh pr create --base main --head dev` cuando el usuario lo pida.
- **Cómo comprobarla**: `gh pr list --base main` no muestra un PR del lote.
- **Pendiente**: la decisión del usuario sobre publicar `v0.1.0` y cargar los secrets del updater ([022-updater](022-updater.md)).

# 027: @types/node sube a 26 (salto de versión mayor)

- **Contexto**: la última estable de `@types/node` es 26.6.7; el client tenía 24.19.2. D-1 pide la última estable, y es un salto de versión mayor de los tipos.
- **Elegida**: 26.6.7 exacta. `bun run --cwd client typecheck`, los 1668 tests y el build pasan sin cambios de código.
- **Descartadas**: quedarse en 24.x (contradice D-1); un rango `^` (la regla lo prohíbe).
- **Cómo revertir**: en `client/package.json`, `"@types/node": "24.19.2"`, y `bun install`.
- **Cómo comprobarla**: `bun run --cwd client typecheck`.

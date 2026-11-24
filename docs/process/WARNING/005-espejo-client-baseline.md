# 005: la auditoría del espejo de client arranca con un baseline de 8 módulos sin test

- **Contexto**: D-9 pide la auditoría del espejo de `client/tests/unit/src`, con la lógica de la 003. Al activarla, 8 módulos de `client/src` no tienen test en su ruta espejo (`app/Shell.tsx`, `app/nav.ts`, `app/routes.ts`, `features/queue/JobRow.tsx`, `features/queue/useQueue.ts`, `shared/api/errors.ts`, `shared/hooks/useSetting.ts`, `shared/theme/useTheme.ts`). Varios se prueban de forma indirecta, pero ninguno tiene su espejo.
- **Elegida**: el baseline `tests/validators/client-mirror.baseline.json` lista esos 8, igual que el de la 003 para server y devtools. Un módulo nuevo sin test falla, y el baseline solo puede bajar: si un espejo aparece, la auditoría pide quitarlo de la lista.
- **Descartadas**: escribir ahora los 8 tests (fuera del alcance de la 005, y la 006 y la 011 tocan varios de esos módulos); excluir la carpeta entera (dejaría sin auditoría lo nuevo).
- **Cómo revertir**: quitar la llamada a `client_mirror.problems` en `client.py` (`unit`) y borrar el baseline.
- **Cómo comprobarla**: `uv run pytest devtools/tests/unit/test_runner/test_client_mirror.py` y `python -m devtools test-runner --type=client-unit`.
- **Pendiente**: ficha en `PENDING/` cuando una spec posterior toque cualquiera de los 8.

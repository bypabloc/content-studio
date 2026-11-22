# 012: la aceptación de la bienvenida y las capturas no dependen de una ventana manual

- **Contexto**: el criterio 7 de `03-verificacion-final.md` pide abrir la app con una base nueva y recorrer la bienvenida a mano. El agente no puede lanzar la ventana: la herramienta de escritorio bloquea PowerShell. El criterio 8 pide capturas que revisa `image-reader`. El usuario dejó de estar disponible para decidir.
- **Elegida**: la bienvenida se prueba con la e2e `tests/e2e/welcome/happy-first-run.e2e.ts` (Playwright sobre el build, API simulada) y con las pruebas unitarias de `WelcomeGate` y `WelcomeWizard`. Pasa `test-runner --type=e2e` (log `logs/test-runner-e2e-012.log`). La revisión visual con una base real y las capturas quedan en `PENDING/012-instalar-motor-real.md`, que no bloquea la fusión.
- **Descartadas**: esperar al usuario (la spec se ejecuta sin detenerse); lanzar la app con un `.cmd` por PowerShell sin verla (no prueba nada visual); marcar el criterio como cumplido sin prueba (no es honesto).
- **Cómo revertir**: borrar el test de `happy-first-run` no revierte nada del producto; la revisión visual sigue pendiente en PENDING.
- **Cómo comprobarla**: `python -m devtools test-runner --type=e2e` y `python -m devtools test-runner --type=all`.
- **Pendiente**: [012-instalar-motor-real](../PENDING/012-instalar-motor-real.md).

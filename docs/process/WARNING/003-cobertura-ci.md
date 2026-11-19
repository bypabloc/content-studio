# 003: la cobertura y el espejo se midieron en Windows; la CI (Linux) aún no corrió

- **Contexto**: `coverage.baseline.json` (18 archivos) y `mirror.baseline.json` se generaron en Windows. Las ramas `sys.platform` y los módulos de terminal (`termios`, consola de Windows) cubren distinto en Linux, así que la CI puede marcar archivos que aquí pasan.
- **Elegida**: aceptar la medición de Windows como base y dejar que la primera corrida de `calidad` en el PR sea la prueba. Si un archivo queda bajo el 80 % solo en Linux, se añade a `coverage.baseline.json` en el mismo PR, con su porcentaje en el mensaje del commit. El 80 % no se baja.
- **Descartadas**: medir solo en Linux desde WSL antes del PR (el entorno de trabajo es Windows, y el venv de WSL no está preparado); excluir `sys.platform` del cálculo (esconde código de Windows).
- **Cómo revertir**: quitar `coverage.baseline.json` y dejar que la etapa falle en todo lo que no llegue al 80 %, o ajustar el alcance (`in_scope`).
- **Cómo comprobarla**: `gh pr checks <n>` con `calidad` verde en 3.10 y 3.12. Localmente, `python -m devtools test-runner --type=unit --git-mode=all` pasa.
- **Pendiente**: que el PR de la 003 muestre `calidad` en verde antes del merge a `dev`. Si no, esta ficha se actualiza con los archivos y las medidas de Linux.

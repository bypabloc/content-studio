# 010: la etapa `budget` mide solo el JS de arranque (entrada y `modulepreload`), no los chunks de `import()`

- **Contexto**: con la pantalla de grabar, el JS total llegó a 234,78 kB gzip, por encima de 232 kB. `budget.py` sumaba todos los `assets/*.js`, también los chunks de `import()` que no bajan al abrir la app. La ficha PENDING 010-presupuesto-solo-arranque fijaba este cambio para antes de la 7c si el bundle pasaba el límite.
- **Elegida**: medir el script de entrada y sus `modulepreload` de `client/dist/index.html`, cada archivo comprimido por separado, como viaja por la red. El límite de `client/budget.json` no cambia (232 kB). Sin `index.html` o sin script de entrada, la etapa falla: no puede pasar con 0 kB. La regla `frontend-stack.md` y su copia en `.claude/` dicen ahora 232 kB, no 250.
- **Descartadas**: subir el límite (la cifra dejaría de decir algo y el chunk diferido la inflaría igual); usar solo `lazy()` (la medida antigua contaba los chunks igual); medir solo el archivo más grande (no sigue lo que baja el arranque).
- **Cómo revertir**: volver a sumar `dist/assets/*.js` en `devtools/test_runner/budget.py` y restaurar sus pruebas.
- **Cómo comprobarla**: `uv run pytest devtools/tests/unit/test_runner/test_budget.py` y la etapa `budget` del gate; `tmp/budget/report.json` lista solo los archivos del arranque.
- **Pendiente**: ninguno. Cierra la ficha PENDING 010-presupuesto-solo-arranque y sustituye la medida de 010-presupuesto-del-cliente.

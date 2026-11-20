# 010: medir solo el JS de arranque en la etapa `budget`, y corregir el límite que dice `frontend-stack.md`

- **Qué queda**: `devtools/test_runner/budget.py` mide todo el JS del build, aunque `client/budget.json` lo llame `initialJsGzipKb`. Cuando una pantalla se cargue con `import()`, esa medida la castiga aunque no pese al arranque, y además cada chunk se comprime por separado. Hace falta medir solo el script de entrada y sus `modulepreload` de `client/dist/index.html`, y ajustar sus pruebas (`devtools/tests/unit/test_runner/test_budget.py`).
- **Por qué no ahora**: cambia el significado de la etapa para todo el proyecto. Va en una spec propia o en la verificación integral (016), con su ficha de WARNING.
- **Además**: `.agents/rules/frontend-stack.md` (y su copia en `.claude/rules/`) dice «250 kB gzip», mientras `client/budget.json` tiene el límite vigente (232 kB tras la ficha WARNING `010-presupuesto-del-cliente`). Corregir la regla al límite real, y sincronizar con `python -m devtools rules --sync`.
- **Cuándo**: antes de la 7c si el bundle pasa de 232 kB; en cualquier caso, en la 016.
- **Quién**: Agente.

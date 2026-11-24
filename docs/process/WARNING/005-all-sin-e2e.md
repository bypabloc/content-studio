# 005: `all` incluye budget y deja e2e fuera

- **Contexto**: D-9 dice que `all` incluye las etapas del client y `e2e`; el T1 decidió que `e2e` va aparte. e2e necesita Chromium instalado, y `all` corre en la calidad de cada PR (ubuntu, con Python 3.10 y 3.12).
- **Elegida**: `all` = calidad + `client-lint`, `client-typecheck`, `client-unit` y `budget` (solo `vite build`, sin navegador). `e2e` va en el job `client` de `calidad.yml`, que instala Chromium, y en la batería de AC-9.
- **Descartadas**: meter e2e en `all` (la calidad de Python instalaría Chromium dos veces y `all` local fallaría en un equipo sin navegador); dejar `budget` fuera (el presupuesto no se vería en cada PR).
- **Cómo revertir**: añadir `'e2e'` a `GROUPS['all']` en `devtools/test_runner/main.py` y `playwright install` al job `calidad`.
- **Cómo comprobarla**: `uv run pytest devtools/tests/unit/test_runner/test_main.py` (`test_all_includes_budget_and_leaves_e2e_out_because_it_needs_chromium`) y el job `client` de la CI.

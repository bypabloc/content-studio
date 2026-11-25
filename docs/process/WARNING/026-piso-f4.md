# 026: la fase de piso (F4) no tiene commit propio

- **Contexto**: el piso de los motores ya es 3.11 (`pyproject.toml`: `target-version` y `python_version`) desde `9908005` (F3), al cambiar las recetas. El plan de F4 pedía un RED con el piso viejo, pero ese estado ya no existe.
- **Elegida**: no hacer commit de F4. AC-5 lo cubre `tests/validators/test_structure.py::test_ac3_floor_comes_from_recipes` (de la 025): compara `target-version` y `python_version` con `engine_floor()`. Gate verde: `ruff check`, `ruff format --check` y `pytest` (2183 pasan).
- **Descartadas**: renombrar el test al del plan (`test_ac3_piso_sale_de_las_recetas`): solo cambiaría el nombre. Aplicar reglas `UP` nuevas: con piso 3.11, `ruff check` no reporta nada.
- **Cómo revertir**: quitar el cambio de `pyproject.toml` de `9908005`; el test de estructura falla.
- **Cómo comprobarla**: `uv run pytest tests/validators/test_structure.py -k floor`.

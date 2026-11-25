# 025: nombres de tests y funciones nuevos en inglés

- **Contexto**: el spell check del pre-commit corre en inglés sobre `tests/validators/` y `devtools/`, y marca los identificadores en español (`versiones`, `archivo`, `receta`). `textos-e-idioma.md` manda identificadores en inglés; los docstrings siguen en español.
- **Elegida**: los tests y funciones nuevos llevan nombre en inglés y conservan el número de AC (`test_ac2_versions_match`). Los nombres del README y del plan de la fase 1 se actualizan.
- **Descartadas**: `# cspell:ignore` palabra por palabra (ensucia cada archivo); nombres en español (violan la regla de identificadores).
- **Cómo revertir**: renombrar de vuelta en el commit de la fase 1 (no cambia comportamiento).
- **Cómo comprobarla**: `python -m devtools test-runner --type=spelling` y el pre-commit sobre los archivos staged.
- **Pendiente**: ninguno.

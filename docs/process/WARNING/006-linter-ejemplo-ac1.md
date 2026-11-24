# 006: el ejemplo del AC-1 lleva punto final, para que la regla 3 no lo marque

- **Contexto**: el AC-1 dice que «Hola; esto es DEMO con 24 horas» devuelve las reglas 6, 2 y 13. Ese texto no termina en punto, y la regla 3 de `formato-guion.md` (toda oración termina en `.`, `?` o `!`) lo marcaría también. Las dos cosas no pueden ser verdad a la vez.
- **Elegida**: el caso de prueba y el de la ruta usan «Hola; esto es DEMO con 24 horas.» (con punto). El linter aplica la regla 3 tal como está escrita en la guía.
- **Descartadas**: quitar la regla 3 del linter (dejaría pasar oraciones sin cierre, que la guía marca como error); revisar la regla 3 solo entre párrafos (la última oración de un texto quedaría sin revisar).
- **Cómo revertir**: quitar el punto final del caso en `server/tests/unit/src/content_studio/narration/test_script_lint.py` y en `api/routes/test_narration.py`. Sin el punto, el resultado incluye también la regla 3.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/narration/test_script_lint.py::test_ac1_the_spec_example_gives_rules_6_2_and_13_in_order`.
- **Antes de**: el merge a `dev`.

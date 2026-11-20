# 006: la regla 2 usa una lista corta de siglas en `script_lint.py`, porque el repo no tiene diccionario

- **Contexto**: la regla 2 (nada de mayúsculas para dar énfasis) excluye «las siglas del diccionario». Buscado en `server/src`, no hay ningún diccionario de siglas: `narration/evaluation/compare.py` solo tiene el nombre de cada letra («pe de efe»).
- **Elegida**: una constante `ACRONYMS` en `script_lint.py` (el identificador va en inglés) con doce siglas comunes (PDF, DNI, IVA, CEO, ONG, SMS, URL, GPS, USB, API, HTML, ONU). Cualquier otra palabra de 3 letras o más en mayúsculas se marca como énfasis.
- **Descartadas**: un archivo JSON aparte (una fuente más para una lista de doce nombres); no marcar ninguna mayúscula (dejaría pasar «DEMO», el ejemplo del AC-1).
- **Cómo revertir**: vaciar la constante; las siglas volverían a marcarse.
- **Cómo comprobarla**: `test_ac1_rule_2_flags_uppercase_emphasis_but_not_acronyms` (`PDF` no se marca y `DEMO` sí).
- **Antes de**: el merge a `dev`.

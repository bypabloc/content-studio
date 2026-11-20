# 010: AC-10 busca rutas y dependencias del grabador, no la palabra «grabar»

- **Contexto**: AC-10 pide que `grabar`, `questionary` y `rich` no aparezcan en lo versionado (sin docs). La palabra «grabar» es también el texto de la UI nueva («Grabar», «Crea uno para grabar»), así que buscarla sola daría falsos positivos.
- **Elegida**: el test busca `narration/grabar`, `narration.grabar`, `grabar/` (la ruta del paquete viejo), `questionary` y `rich` como palabra. Excluye `*.md`, `docs/` y `uv.lock`: el lock es generado y puede traer `rich` como dependencia transitiva de otra herramienta; lo que cuenta son las referencias del proyecto.
- **Descartadas**: buscar `grabar` a secas (marca los textos de la UI) y excluir solo `docs/` (dejaría pasar `.agents/rules` y los READMEs de datos, que sí son referencias del proyecto).
- **Cómo revertir**: quitar `test_ac10_no_legacy_recording` de `tests/validators/test_structure.py`.
- **Cómo comprobarla**: `uv run pytest tests/validators/test_structure.py::test_ac10_no_legacy_recording`.

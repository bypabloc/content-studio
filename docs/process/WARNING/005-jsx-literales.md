# 005: AC-8 se comprueba con la regla `react/jsx-no-literals` de oxlint, como error

- **Contexto**: AC-8 pide que ningún texto visible esté escrito directamente en un `.tsx`. cspell no lo puede comprobar porque `client/**` acepta español a propósito (el catálogo y los comentarios van en español). Hoy no hay ningún literal, pero nada lo impedía.
- **Elegida**: `react/jsx-no-literals` como `error` en `client/.oxlintrc.json`, dentro de `client-lint`. El único caso que marcó fue el símbolo de agarre `⋮⋮` de `JobRow.tsx`, que ahora va como expresión (`{'⋮⋮'}`).
- **Descartadas**: un test que escanee los `.tsx` en busca de palabras en español (frágil con los acentos y con los identificadores); dejarlo solo a la revisión (AC-8 pide verificación).
- **Cómo revertir**: quitar `"react/jsx-no-literals": "error"` de `client/.oxlintrc.json`.
- **Cómo comprobarla**: `bun run --cwd client lint` (sale con código 0 y ningún aviso de `jsx-no-literals`).

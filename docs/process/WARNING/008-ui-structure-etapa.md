# 008: la etapa `ui-structure` bloquea etiquetas nativas fuera de átomos; tres restos de moléculas se resolvieron

- **Contexto**: D-5 pide la etapa `ui-structure` con el compilador de TypeScript, no con grep. Al correrla con `--git-mode=all`
  quedaban `fieldset`, `legend` (en `UIDateParts`) y `time` (en `UITimeline`), que la revisión de T6 no había visto.
- **Elegida**:
  - La regla es la de la spec: un elemento JSX en minúscula, un `createElement` con cadena literal y un `<Tag>` cuya constante
    vale una cadena. Se mira `client/src/**/*.tsx` entero. Las carpetas exentas son `atoms/` y `shadcn/`, por nombre de carpeta:
    un archivo que se llama `atoms.tsx` no cuenta.
  - La etapa ignora la lista de archivos, como `client-lint` e `i18n`: el análisis de todo `client/src` cuesta segundos.
  - `fieldset` y `legend` → `UIBox role="group"` con `aria-labelledby` apuntando a un `UIText` con `id`: el grupo conserva su nombre.
  - `time` → átomo nuevo `atoms/UITime`, con `dateTime` y su test espejo. El AC «fecha como time» lo pide.
  - REFACTOR del ciclo 7: no se crea `client/scripts/ts-program.ts`. `loose-texts.ts` solo lee el archivo y crea su
    `SourceFile`; son tres líneas, y compartirlas no ahorra nada.
- **Descartadas**:
  - `react/forbid-elements`: exige listar cada etiqueta, no distingue carpetas y no ve `createElement` (D-5).
  - Un `grep` de `<[a-z]`: falsos positivos con los genéricos de TypeScript.
  - Un marcador `ui-structure-ignore`: la spec dice «sin excepciones»; lo que haga falta va a un átomo.
  - Dejar `fieldset` o `time` en las moléculas: rompe D-4.
- **Cómo revertir**: quitar `ui-structure` de `STAGES`, de `GROUPS['all']`, del script de `client/package.json` y de la línea
  de client del pre-commit. El `time` vuelve a la molécula solo si se quita también la regla.
- **Cómo comprobarla**: `uv run pytest devtools/tests/unit/test_runner/test_ui_structure.py -q` (seis casos) y
  `python -m devtools test-runner --type=ui-structure --git-mode=all` con 0 hallazgos.
- **Antes de**: el merge a `dev`.

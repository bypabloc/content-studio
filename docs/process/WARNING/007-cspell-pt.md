# 007: el diccionario de portugués de cspell es una dependencia de desarrollo de la raíz

- **Contexto**: `pt.json` se revisa con ortografía en portugués, y cspell no trae ese diccionario de serie.
- **Elegida**: `@cspell/dict-pt-br` como dependencia de desarrollo de la raíz (igual que `@cspell/dict-es-es`), importada en `cspell.config.yaml` con el override de `pt.json` (`en,pt-br`).
- **Descartadas**:
  - Un diccionario copiado al repo: se desactualiza y no lo mantiene nadie.
  - No revisar `pt.json` en portugués: los errores de ortografía de una traducción pasarían sin verse.
- **Cómo revertir**: quitar la dependencia de `package.json` y el `import` de `cspell.config.yaml`; `pt.json` pasa a revisarse en `en`.
- **Cómo comprobarla**: `python -m devtools test-runner --type=spelling` pasa con `pt.json`, y la prueba `test_ac10_spelling_passes_on_the_real_catalogs` lo afirma.
- **Antes de**: el merge a `main`. Confirmar la licencia del paquete (MIT) con el resto de dependencias de desarrollo; no bloquea el uso local.

# 008: `UIDateRangePicker` formatea las fechas con `Intl` en `es` fijo

- **Contexto**: el calendario de klinikae formatea nombres de mes y de día con `Intl` en `es`. content-studio tiene tres idiomas (es, en, pt): con otro idioma activo, el calendario seguiría en español.
- **Elegida**: en T4 el organismo queda con `es` fijo, para no mezclarlo con la migración de textos. El idioma activo llega por props cuando el shell lo tenga (T5).
- **Descartadas**: leer el idioma desde `shared/i18n` dentro del organismo: lo acoplaría al estado global.
- **Cómo revertir**: no aplica; se cambia en T5.
- **Cómo comprobarla**: `bun run --cwd client test -- DateRangePicker` (los nombres salen en español). Con el idioma en inglés, el cambio se verifica en T5.
- **Antes de**: el cierre de la 008 (T5).

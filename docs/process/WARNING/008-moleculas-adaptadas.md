# 008: adaptaciones de las moléculas: el selector recordado sobre UISelect, el tema controlado por el shell y los tests por rol

- **Contexto**: `RecommendedSelect` es hoy un `<select>` nativo. D-3 lo quiere como `UIRecommendedSelect` sobre `UISelect`, que es un combobox de Base UI. `NarrationOptions` usa `hint` y `disabled` por opción (un motor sin instalar).
- **Elegida**:
  - `UISelect` y `SearchSelectOption` suman `description` (la pista) y `disabled` por opción; el `Picker` pasa `disabled` a cada `ComboboxItem`. Son campos opcionales: el resto del comportamiento de klinikae no cambia.
  - `UIRecommendedSelect` conserva la API de `RecommendedSelect` (`settingKey`, `label`, `options`, `onChange`, `beforeChange`) y la persistencia con `useSetting`. La ★ va en el texto de la opción recomendada, y su descripción es `t('select.recommended')`.
  - El `Picker` se carga con `lazy()`, como en klinikae. Los tests esperan al combobox con `findByRole`, no con `getByRole` síncrono.
  - `UIThemeToggle` queda controlado por props. El shell (T5) lee y guarda la preferencia con `useTheme` de `shared/theme`. Se quitan `next-themes` y `use-hydrated`; su test de HTML estático (solo SSR) se reemplaza por una aserción del ícono y el título de la preferencia recibida.
  - `UIText` no reenvía atributos (`data-*`, `aria-*`). El pill de `UIStatCard` pasa a `UIBox as="span"`, que sí los acepta.
  - `UIToaster` lee el tema con `useTheme`, que pide el provider de settings. Su test fija el tema con un mock.
  - Los tests de klinikae que afirmaban `dl`, `table`, `ol` o `closest('li')` pasan a roles ARIA (ver `008-moleculas-nativas`). Mismos casos, misma intención.
  - Las moléculas no traen textos por defecto: klinikae los recibe por props (`labels`), así que T3 no agrega claves `ui.*`. Los textos por defecto de klinikae (cerrar un diálogo, el calendario) están en organismos y se resuelven en T4.
  - `LicenseDialog` sigue en la raíz de `shared/components/`. No es un átomo, una molécula ni un organismo de D-3: se ubica en T4 o T6.
- **Descartadas**:
  - Un `RecommendedSelect` propio con `<select>`: rompe AC-2 y D-3.
  - `useTheme` dentro de `UIThemeToggle`: obligaría a todos sus tests y a todos sus usos a montar el provider de settings.
- **Cómo revertir**: los campos `description` y `disabled` son opcionales; quitarlos deja `UISelect` como en klinikae, pero `UIRecommendedSelect` pierde la pista y la opción deshabilitada.
- **Cómo comprobarla**: `bun run --cwd client test -- components/molecules` (`UIRecommendedSelect`: 8 casos; `UIThemeToggle`; `UIToast`).
- **Antes de**: el merge a `dev`.

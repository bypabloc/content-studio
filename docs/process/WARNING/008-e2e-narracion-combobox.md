# 008: los e2e de narración esperan el combobox del motor, no un select nativo

- **Contexto**: desde T3 (`ae7b877`) la pantalla de Narración usa `UIRecommendedSelect`, que se apoya en `UISelect` (un combobox de Base UI). El motor se muestra con su etiqueta y la ★ del recomendado («★ voxcpm2»). Los tests de 006 (`happy-generate`, `happy-import-batch` y `neg-license-cancel`) esperaban un `<select>` nativo: `toHaveValue('voxcpm2')` y `selectOption('omnivoice')`. El e2e no corrió en T1–T4 porque `test-runner --type=all` lo deja fuera (`005-all-sin-e2e`), así que la regresión apareció al verificar T5.
- **Elegida**: los tests se ajustan a lo que ve el usuario: el valor se compara con `/voxcpm2/` y el motor se elige abriendo el combobox y pulsando la opción por su nombre. La app no cambia.
- **Descartadas**: quitar la ★ del valor mostrado (cambia D-4, que pide la estrella en el recomendado); saltar los tests (esconde la regresión).
- **Cómo revertir**: volver a `selectOption` y a `toHaveValue('voxcpm2')` solo si `UISelect` vuelve a ser un select nativo.
- **Cómo comprobarla**: `python -m devtools test-runner --type=e2e` (16 pruebas, exit 0). El e2e se corre a mano en cada spec de la 008 mientras no esté en `all`.
- **Pendiente**: ninguno.

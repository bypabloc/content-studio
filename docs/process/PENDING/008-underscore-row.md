# 008: `_row` en UIRowTable y UIRepeatGroup da avisos de no-underscore-dangle

- **Qué**: los dos organismos usan `item._row` como clave de cada fila. `bun run --cwd client lint` da tres avisos `no-underscore-dangle` en cada archivo (`organisms/UIRowTable/index.tsx` y `organisms/UIRepeatGroup/index.tsx`). Son avisos, no errores: el lint sale con 0.
- **Por qué no se hizo**: el nombre `_row` viene de klinikae. Renombrarlo cambia la forma de los datos que reciben los dos organismos, y no bloquea nada.
- **Cuándo**: al tocar esos organismos, o antes de la 022.
- **Quién**: agente.
- **Qué la cierra**: renombrar la clave (por ejemplo, `rowId`) en los dos organismos y en sus usos, o permitir `_row` en `client/.oxlintrc.json` con una ficha WARNING.

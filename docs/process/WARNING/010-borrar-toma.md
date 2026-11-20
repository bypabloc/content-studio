# 010: borrar una toma la manda a la papelera del perfil, y la referencia elegida no cambia

- **Contexto**: el usuario no podía borrar una toma ya grabada: en cada toma solo había «Elegir».
- **Elegida**: botón «Borrar toma» en cada toma, con confirmación. La toma y su `<n>.check.json` se mueven a `reference/.trash/<fecha>/<perfil>/takes/<estilo>/`. `DELETE /voices/profiles/{slug}/takes/{style}/{take}` responde 204, y 404 si la toma no existe.
- **Descartadas**: el borrado definitivo. Borrar un perfil ya va a la papelera y nunca borra bytes; una toma sigue el mismo criterio.
- **Por qué la referencia no cambia**: elegir una toma la copia a la referencia del estilo (`copy2`). Borrar la toma no toca esa copia.
- **Cómo revertir**: quitar la ruta `delete_take` de `api/routes/voices.py`, `profile_takes.trash` y el botón de `TakeRow`.
- **Cómo comprobarla**: `test_voices.py`, «a take goes to the trash with its check and the chosen reference stays» y «deleting a take that is not there is 404»; `TakeRow.test.tsx`, borrar pide confirmación y manda el DELETE, y cancelar no toca la toma.

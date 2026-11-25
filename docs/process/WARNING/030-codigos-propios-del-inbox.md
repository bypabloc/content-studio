# 030: los códigos de error del inbox tienen nombre propio

- **Contexto**: 02 §2 y §5 piden `folder_not_found` y `unknown_kind`. Ya existen en el catálogo con otro sentido: `folder_not_found` dice «La carpeta {folder_id} no está en la biblioteca» y `unknown_kind` dice «No existe el tipo de trabajo».
- **Elegida**: códigos propios. `inbox_path_not_found` (la ruta no existe), `inbox_kind_not_accepted` (el tipo existe pero no acepta archivos sueltos), `inbox_folder_already_registered` e `inbox_folder_not_found` (404 con el id). `unknown_kind` queda solo para un tipo que no existe. Los textos están en los tres catálogos.
- **Descartadas**: cambiar el texto del código de la biblioteca (rompería la biblioteca y su prueba); usar los códigos de 02 tal cual (el texto saldría mal para una carpeta).
- **Cómo revertir**: renombrar los códigos en `inbox/store.py` y `api/routes/inbox.py`, y sus textos en `messages/`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/api/routes/test_inbox.py server/tests/unit/src/content_studio/cli/test_inbox.py`.

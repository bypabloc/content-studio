# 032: POST /uploads recibe el archivo crudo con ?name=, no multipart

- **Contexto**: 02 §2 dice «multipart». Con `UploadFile`, FastAPI guarda todo el archivo antes de llamar a la ruta, así que el tope de `api.lan.max_upload_mb` (2048) se aplicaría después de escribir hasta 2 GB.
- **Elegida**: el cuerpo es el archivo (`application/octet-stream`) y el nombre va en `?name=`. La ruta escribe por partes y corta con 413 `upload_too_large` al pasar el tope, sin dejar el archivo a medias. También rechaza antes un `Content-Length` mayor. El nombre se limpia con `guard.safe_name` y se guarda en `<salidas>/uploads/<dispositivo>/<azar>-<nombre>`. Ejemplo: `curl -k -X POST "https://<ip>:41831/uploads?name=voz.wav" -H "Authorization: Bearer <token>" --data-binary @voz.wav`.
- **Descartadas**: multipart con `UploadFile` (tope tardío y copia temporal). Un límite en el proxy (no hay proxy).
- **Cómo revertir**: cambiar la firma de `api/routes/uploads.py::upload` a `UploadFile`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/api/routes/test_uploads.py -q`.

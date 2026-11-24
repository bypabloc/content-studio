# 020: dependencia nueva `send2trash` para la papelera

- **Contexto**: la Biblioteca nunca borra de forma definitiva: lo que el usuario borra va a la papelera del sistema para poder restaurarlo (D-4). La stdlib no tiene una API de papelera.
- **Elegida**: `send2trash>=2.2.0` (licencia BSD, Python puro, usa `IFileOperation` en Windows), en `server/pyproject.toml`. Se importa solo dentro de `library.actions.send_to_trash`; en CI se simula y la prueba `-m local` la usa de verdad.
- **Descartadas**: `ctypes` con `SHFileOperationW` a mano (código de plataforma que hay que mantener); `os.remove` (borra sin vuelta atrás, contra la decisión del usuario).
- **Cómo revertir**: `uv remove send2trash` en `server/`, y quitar `send_to_trash` de `library/actions.py` y esta ficha.
- **Cómo comprobarla**: `uv run pytest -m local server/tests/unit/src/content_studio/library/test_actions.py` y revisar la papelera de Windows.
- **Pendiente**: ninguna.

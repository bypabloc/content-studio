# 004: el candado de GPU vive en el server y devtools lo importa

- **Contexto**: `gpu-turn` (devtools, solo stdlib) y el worker de la cola tienen que tomar el mismo turno de la GPU. Con dos copias, el candado podía dejar de coincidir entre el CLI y el server.
- **Elegida**: `server/src/content_studio/gpu_lock.py` (solo stdlib). `devtools` lo importa agregando `server/src` al `sys.path`. El CLI `studio` y el worker toman el candado solos: el candado no es reentrante, así que `studio` no se envuelve en `gpu-turn run` (tomaría el candado dos veces; ver `turno-gpu.md`).
- **Descartadas**: dos copias del candado (pueden divergir); que el server importe `devtools` (el server no debe depender del flujo de agentes).
- **Cómo revertir**: restaurar la copia de `devtools/gpu_turn.py` anterior a `98ba38c` y quitar `gpu_lock.py` del server.
- **Cómo comprobarla**: `python -m devtools gpu-turn status` (exit 0 libre) y `uv run pytest server/tests/unit/src/content_studio/test_gpu_lock.py`.
- **Pendiente**: ninguno.

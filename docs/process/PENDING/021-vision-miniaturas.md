# 021: usar la visión de Gemma 4 para elegir miniaturas

- **Qué**: Gemma 4 E4B es multimodal (imagen y audio). El asistente de la 021 solo usa texto; quedan fuera elegir la miniatura de un video, describir cuadros o evaluar el audio.
- **Por qué no se hizo**: el usuario no lo pidió en la 021 (fuera de alcance). Requiere el `mmproj` del modelo (unos 1 GB más) y `llama-server --mmproj`.
- **Cuándo**: si el usuario lo pide.
- **Quién**: usuario (decide); agente (implementa).
- **Qué la cierra**: una spec con la tarea `llm.thumbnail`, el `mmproj` en la receta de `gemma-4-e4b` y su prueba con un video real.

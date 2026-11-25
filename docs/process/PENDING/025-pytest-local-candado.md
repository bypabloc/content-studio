# 025: `gpu-turn run -- pytest -m local` se bloquea con el test de llm

- **Qué**: envolver `pytest -m local` en `gpu-turn run` deja colgado `test_local_llama_server_answers_a_json_with_the_recommended_model`: el test toma el candado con `gpu_lock.acquire(..., wait=True)` y espera a su propio proceso, que ya lo tiene.
- **Por qué no se hizo**: la spec 025 corre la suite local sin envoltorio para ese test y con envoltorio para el resto. Es un fallo de diseño del test, fuera del alcance de la 025.
- **Cuándo**: en la próxima spec que toque el turno de la GPU o los tests `-m local`.
- **Quién**: agente.
- **Qué lo cierra**: `gpu-turn run -- uv run pytest -m local` completo, sin colgarse: el test respeta un candado heredado o se corre fuera del envoltorio.

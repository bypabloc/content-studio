# 026: asistente: identificar el caso que falla en script_review (1 de 25 en cada modelo)

- **Qué**: mirar qué caso de `script_review` no pasa en gemma-4-e4b y en qwen3.5-9b (con b12686), y si es una respuesta que no valida contra el JSON schema (`llm_invalid_output`) o un criterio de la prueba.
- **Por qué no se hizo**: `llm-eval` guarda el porcentaje y no el detalle por caso; hace falta ampliar la herramienta o repetir los casos a mano.
- **Cuándo**: después de publicar.
- **Quién**: agente.
- **Qué la cierra**: la lista de los casos fallidos con su respuesta, y un caso de regresión si es un fallo de validación.

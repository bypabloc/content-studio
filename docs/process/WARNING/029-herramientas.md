# 029: diez herramientas por tarea, no una por motor

- **Contexto**: 02 §2 y D-2 de la spec 029. Un modelo local chico (Qwen3.5 9B en LM Studio) elige peor entre una lista
  larga, y `studio` tiene varios motores y tipos de trabajo.
- **Elegida**: diez en total. Cinco por tarea (narrar, música, transcribir, limpiar silencios, convertir), más
  `studio_capabilities`, `studio_submit_job` (genérica para cualquier `kind`) y tres para seguir un trabajo (`get`,
  `wait`, `cancel`). La lista está cerrada: AC-1 la fija.
- **Descartadas**: una herramienta por motor o por tipo de trabajo (una lista de más de veinte); solo la genérica
  (el agente tendría que conocer los `params` de cada tipo).
- **Cómo revertir**: quitar las entradas de `mcp_server/catalog.py` y su caso en AC-1.
- **Cómo comprobarla**: `uv run pytest server/tests/integration/test_mcp_bridge.py::test_ac1_protocolo_lista_las_diez_herramientas`.

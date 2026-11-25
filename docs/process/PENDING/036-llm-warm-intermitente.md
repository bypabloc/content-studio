# 036: test_llm_warm intermitente bajo carga

- **Qué**: `server/tests/unit/src/content_studio/jobs/test_llm_warm.py::test_ac2_an_idle_server_stops_and_releases_the_turn` falló una vez en la etapa `unit` completa (la espera `gpu_lock.read(env.main) is None`, con timeout de 10 s). En la pasada siguiente de la misma etapa pasó, y aislado pasó dos veces seguidas.
- **Por qué no se hizo**: no se encontró la causa. La prueba depende de tiempos (`llm.idle_seconds` de 0.6 s) y la fase 2 no toca ese código.
- **Cuándo**: después de publicar.
- **Quién**: agente.
- **Qué la cierra**: diez corridas seguidas de `uv run pytest server/tests/unit/src/content_studio/jobs/test_llm_warm.py` sin fallo, o un cambio que quite la dependencia de tiempos.

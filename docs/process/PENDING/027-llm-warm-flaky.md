# 027: test de tiempo del servidor LLM falló una vez en la suite completa

- **Qué**: `server/tests/unit/src/content_studio/jobs/test_llm_warm.py::test_ac2_an_idle_server_stops_and_releases_the_turn` falló una vez en una suite completa (2185 pasan, 1 falla) y pasó 3 de 3 corrido solo.
- **Por qué no es de 027**: la 027 no toca Python. Es un test con espera por tiempo (`_wait_for`) y la suite estaba cargada.
- **Quién decide**: agente.
- **Qué lo cierra**: que el test espere por condición con un plazo mayor, o se marque como intermitente con su causa. Revisar si vuelve a fallar en un gate.

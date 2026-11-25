# 028: un fallo intermitente en la suite completa (no reproducido)

- **Qué**: en una pasada completa de `uv run pytest` falló 1 test (no se conservó su nombre). La pasada siguiente dio 2218 pasados. Los tests nuevos de la 028 arrancan procesos reales y esperan por tiempo.
- **Quién decide**: agente.
- **Qué lo cierra**: que una suite completa salga limpia tres veces seguidas, o que el fallo se reproduzca y se corrija su causa.

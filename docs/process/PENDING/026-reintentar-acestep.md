# 026: acestep en Python 3.13 o más cuando su pyproject lo permita

- **Qué**: subir acestep a una versión de Python más alta cuando el upstream permita 3.13 o más y su torch 2.7.1 tenga rueda para esa versión (o cuando suban torch).
- **Por qué no se hizo**: el `requires-python` del upstream es `>=3.11,<3.13` y el pin de torch es `2.7.1`.
- **Cuándo**: después de publicar.
- **Quién**: agente.
- **Qué la cierra**: instalación y pista de 30 s correctas en la versión nueva, con `voice: false` en `tracks.json`.

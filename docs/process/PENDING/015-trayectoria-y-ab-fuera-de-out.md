# 015: pendientes de las pantallas (T7)

**Qué falta.**

- **Dibujar la trayectoria de «Seguir a la persona» sobre la línea de tiempo** (plan, ciclo 7, D-6). La pantalla analiza las caras y espera el `track.json`, pero no muestra la trayectoria. Falta un componente que lea `track.json` (con `GET /files?path=`) y lo dibuje sobre la forma de onda o la línea de tiempo. Se hace con la vista previa del Editor (017), que ya tiene la línea de tiempo.
- **A/B de Normalizar con un original fuera de `out/` y `reference/`.** `GET /files` solo sirve esas carpetas (`api/paths_guard.py`). Si el usuario normaliza un archivo que está en otra carpeta, el original no se puede reproducir y el A/B falla en silencio. El resultado sí se reproduce (está en `out/`). Hay que decidir si se sirve el original o se copia a `tmp/` al encolar; se confirma en el e2e `normalize/happy-podcast-ab` (T8).

**Por qué no se hizo ahora.** La trayectoria depende de la línea de tiempo del Editor, y el A/B del original es una decisión de acceso a archivos que toca la API de `/files`, fuera del alcance de T7.

**Cómo se verifica.** La trayectoria, con una captura revisada por `image-reader`. El A/B, con un video de fuera de `out/` en el e2e de T8.

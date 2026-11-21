# Módulos implementados

Una ficha por módulo funcional, de hasta 40 líneas, con front-matter `modulo` y `actualizada` y las secciones «Qué resuelve», «Qué hace hoy», «Dónde vive» e «Historial». La actualiza el último commit de cada spec funcional que lo toca.

| Módulo | Qué resuelve | Ficha |
| :--- | :--- | :--- |
| Narración | Voz en off en español neutro clonando una voz de referencia | [narration.md](narration.md) |
| Música | Música de fondo instrumental por estilo | [music.md](music.md) |
| Servidor | API local y cola de trabajos, con el CLI `studio` | [server.md](server.md) |
| Cliente | Ventana de escritorio: shell, cola, tema, selectores y ajustes | [client.md](client.md) |
| Motores y almacenamiento | Instalación de motores con recetas y carpetas elegibles | [engines.md](engines.md) |

## Plantilla

```markdown
---
modulo: <nombre>
actualizada: YYYY-MM-DD
---

# <Módulo>

## Qué resuelve
## Qué hace hoy
## Dónde vive
## Historial
- YYYY-MM-DD: <cambio> (spec <NN>, PR #<n>)
```

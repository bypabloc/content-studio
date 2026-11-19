# Estado del proyecto y hoja de ruta (`docs/process/`)

Fuente del progreso de content-studio: qué hace hoy, qué viene después y qué queda pendiente. Ante una consulta sobre el estado o el roadmap, empieza aquí. A diferencia de [`docs/specs/`](../specs/README.md) (planes efímeros que se borran al implementarse), esta carpeta se mantiene con `dev`. Regla: [`project-progress.md`](../../.agents/rules/project-progress.md).

```text
docs/process/
├── README.md
├── 01-done/     # una ficha por módulo funcional
├── 02-next/     # lo siguiente, una tarea por archivo (prioridad = número)
├── 03-later/    # largo plazo, misma plantilla que 02-next
├── WARNING/     # decisiones de los agentes y lo que se revisa antes de pasar a main
└── PENDING/     # lo que se revisa después y no bloquea
```

| Carpeta | Contenido | Estado |
| :--- | :--- | :--- |
| [01-done](01-done/README.md) | Funcionalidades fusionadas a `dev`, una ficha por módulo | IMP |
| [02-next](02-next/README.md) | Planes próximos aún sin spec | PEN |
| [03-later](03-later/README.md) | Planes de largo plazo | PEN |
| [WARNING](WARNING/README.md) | Decisiones tomadas al ejecutar y lo que hay que aplicar o revisar antes de `main` | PEN |
| [PENDING](PENDING/README.md) | Revisiones posteriores que no bloquean | PEN |

## Ciclo de vida

1. Una idea entra como `02-next/NN-<slug>.md` o `03-later/NN-<slug>.md` con su plantilla.
2. Al decidir implementarla se redacta su spec (skill `crear-spec`) y, en el mismo PR, su tarea sale de `02-next/`.
3. Al fusionarse una spec funcional, su último commit actualiza la ficha del módulo en `01-done/`.
4. Las decisiones de los agentes van a `WARNING/` y lo diferido a `PENDING/`; cada ficha se borra al aplicarla o cerrarla.

# Decisiones y lo que se revisa antes de pasar a `main`

Aquí va cada decisión que un agente tomó solo al ejecutar una spec (`session-handoff.md` §4: la opción correcta, no la más rápida) y todo lo que hay que aplicar o revisar **antes** de publicar en `main`: un venv nuevo que instalar, un modelo que descargar, una licencia que confirmar para uso comercial, un paso manual. Cada ficha se borra al aplicarla, en un PR a `dev`, con su fila. Lo que se revisa **después** va en [`../PENDING/`](../PENDING/README.md).

Nombre: `<spec>-<tema>.md` (sin spec, `<tema>.md`). Formato:

```markdown
# <spec>: <decisión en una línea>

- **Contexto**: qué se encontró y por qué hubo que elegir.
- **Elegida**: la opción y su motivo (la correcta, no la más rápida).
- **Descartadas**: cada alternativa y por qué no.
- **Cómo revertir**: commit o pasos para volver atrás.
- **Cómo comprobarla**: comando o prueba que la confirma.
- **Pendiente**: ficha de `../PENDING/` si deja trabajo para después.
```

| Ficha | Qué | Cuándo |
| :--- | :--- | :--- |
| [001-move-data](001-move-data.md) | `move-data` mueve `narration/` y `music/` a `server/data/` (datos del usuario) y reescribe sus `.pth` | Antes de pasar a `main`: correr `move-data --apply` en el principal, después del `git pull` |
| [002-mapeo-de-nombres](002-mapeo-de-nombres.md) | Mapa de nombres de español a inglés (módulos, datos, valores de salida) y desvíos del plan en el ciclo 4 | Antes de pasar a `main`: revisar el mapa y correr `move-data --apply` (T9) |

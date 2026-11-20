# 010: el build real del catálogo sobre las voces del usuario

- **Qué**: construir (o `Forzar`) voces del catálogo en el principal, sobre las voces del usuario. Reescribe estilos construidos, aprobados y rechazados.
- **Por qué no se hizo**: decisión del usuario, 2026-11-20. AC-7 se cierra con la verificación en copia (`tmp/spec-010/verificar-build-en-copia.py nick`: 10 de 12 estilos aprobados). El paso 2.3 de 03 se cambió en consecuencia.
- **Cuándo**: cuando el usuario lo pida. No bloquea el merge de la 010 ni el pase a `main`.
- **Quién**: usuario. El agente lo ejecuta si el usuario lo autoriza.
- **Qué lo cierra**: `studio narration voices --build <voces>` sobre las voces indicadas, con `aprobacion.json` y los `.wav` revisados. O la decisión de no hacerlo.
- **Cuidado**: `Forzar` regenera la base y todos los estilos desde cero (`build.py`: `new_base = force`). Una voz aprobada puede quedar rechazada, y la narración con `--voice` deja de usarla.

# 007: soltar guiones antes de que cargue el catálogo de motores los descarta sin aviso

- **Qué**: `NarrationPage` encola un guion soltado solo si `ready` (motor y estilo elegidos). Si el catálogo aún no ha cargado, el guion se ignora en silencio; no sale ningún aviso ni se encola.
- **Por qué no se hizo**: el comportamiento es el de la 006 y no cambia el idioma; la prueba e2e lo cubre esperando el motor antes de soltar (`happy-import-batch.e2e.ts`). Arreglarlo cambia el flujo de importación, así que queda fuera de la 007.
- **Cuándo**: en la spec que revise la importación de guiones o la primera vez que el catálogo tarde en cargar en la app real.
- **Quién**: agente.
- **Qué la cierra**: o bien se encola al llegar el catálogo, o bien se muestra un aviso de «todavía cargando» en vez de descartar el guion; con una prueba que suelte antes del catálogo.

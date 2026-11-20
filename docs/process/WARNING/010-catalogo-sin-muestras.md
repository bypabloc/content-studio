# 010: el catálogo trae estado y favorita, y las muestras llegan en el ciclo 7

- **Contexto**: D-5 pide que la ficha del catálogo traiga las muestras por estilo construidas. Para reproducirlas, la UI necesita una URL, y `/files` solo sirve las raíces de `app.state.roots` (`out/` y las referencias). `narration/voices/` no está en esas raíces, y abrirla es un cambio de lectura de archivos fuera de AC-7.
- **Elegida**: `GET /voices/catalog` devuelve la ficha, el estado (`not_built`, `partial` o `approved`) y, por estilo, si está aprobado. La favorita sale de `settings` (`voices.favorites`) como `favorite`. El orden de favoritas primero lo hace el selector de Narración en el ciclo 7, y el build entra por `POST /jobs` con `kind: voice.build`, sin ruta nueva.
- **Descartadas**: añadir `voices/` a `roots` ahora, sin una pantalla que la use; ordenar `/catalog/narration` en el server, que duplica la lógica del selector y AC-9 la verifica en el client.
- **Cómo revertir**: no hay contrato que revertir. En el ciclo 7 se añade la ruta de muestras (y, si hace falta, la raíz en `roots`) y se regenera `schema.d.ts`.
- **Cómo comprobarla**: `uv run pytest server/tests/unit/src/content_studio/api/routes/test_voices_catalog.py` (estado, parcial y favoritas). La corrida real de `voice.build` con una voz queda para la T9.
- **Pendiente**: ninguno fuera de la spec. Las muestras se cierran en el ciclo 7.

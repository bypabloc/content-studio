# 010: el teleprompter pinta en negrita el énfasis del guion (`**palabra**`)

- **Contexto**: el guion marcado de `server/data/narration/docs/scripts/` usa `**negrita**` para el énfasis, y la notación lo explica. El kit lo entrega tal cual.
- **Elegida**: partir el texto por `**` y pintar esas partes en `<strong>`. El resto de las marcas (`/`, `//`, `↗`, `↘`, `→`) se muestra como está.
- **Descartadas**: quitar los asteriscos (se pierde el énfasis); un renderizador de Markdown (una dependencia para una sola marca).
- **Cómo revertir**: mostrar `style.marked` como texto plano en `Teleprompter.tsx`.
- **Cómo comprobarla**: `Teleprompter.test.tsx`, «la negrita del guion (entre dobles asteriscos) se pinta en negrita».
- **Pendiente**: ninguno.

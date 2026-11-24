# 020: qué precarga «Editar y repetir» en cada sección

- **Contexto**: la Biblioteca abre la sección del ítem con `?from_job=<id>` (D-4). Cada sección guarda su estado de otra forma: parte en el formulario y parte en los selectores con recomendado (`select.*` en settings).
- **Elegida**: un hook común (`shared/hooks/useFromJob.ts`) y, por sección, lo que su formulario tiene: Música, los estilos (o el texto libre con tonalidad, BPM y compás), la duración y las opciones avanzadas (AC-7); Narración, el guion; Limpiador, el archivo y los márgenes; Subtítulos y Convertir, el archivo de origen; Mezcla, el proyecto del render. Los selectores con recomendado (motor, voz, estilo, modelo de whisper) no se cambian: son preferencias del usuario y seguirían cambiadas después.
- **Descartadas**: escribir los `select.*` desde `from_job` (pisa la preferencia guardada sin que el usuario lo pida); una pantalla genérica de «repetir con cambios» (duplica cada formulario).
- **Presupuesto**: el catálogo `es.json` con los textos de la Biblioteca llevó el JS inicial a 239,3 kB (límite 237). Mis voces y Catálogo pasan a `lazy()` como las demás secciones; con eso `budget` pasa sin subir el límite.
- **Cómo revertir**: quitar `useFromJob` de cada sección y volver a importar `MyVoicesPage` y `CatalogPage` en `app/Shell.tsx`.
- **Cómo comprobarla**: `bun run --cwd client test` (pruebas `spec 020` de cada sección) y `python -m devtools test-runner --type=budget`.
- **Pendiente**: ninguna.

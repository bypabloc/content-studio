# 017: presupuesto del JS inicial por el catálogo del Editor

- **Contexto**: `client/budget.json` fijaba 236 kB gzip. Las claves nuevas de T7 en `messages/es.json`, que se importa al arranque, llevaron la medición a 236.13 kB. Se reutilizaron claves existentes para los textos duplicados y la medida bajó a 236.09 kB.
- **Elegida**: subir `initialJsGzipKb` a 237 kB. El Editor y sus módulos siguen en carga diferida; el aumento corresponde a los textos en español que el catálogo inicial conserva para todas las secciones.
- **Descartadas**:
  - Reducir código de otras secciones: mezcla cambios sin relación para compensar textos necesarios del Editor.
  - Dividir el catálogo español por sección: añade complejidad al sistema de i18n para ahorrar 0.09 kB; se revisará si otra spec vuelve a agotar el margen.
- **Cómo revertir**: volver a fijar el límite en 236 kB cuando el catálogo se divida por sección o se reduzcan sus claves.
- **Cómo comprobarla**: `python -m devtools test-runner --type=budget`; la medida de T7 es 236.09 kB gzip.
- **Pendiente**: ninguno.

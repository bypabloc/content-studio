# 012: umbral de VRAM y métricas de almacenamiento

- **Contexto**: la spec define tres estados de VRAM y exige espacio usado/libre, pero no fija umbrales ni cómo medir rutas todavía inexistentes.
- **Elegida**: `no entra` si la VRAM detectada es menor al requisito; `justo` desde el requisito hasta menos de 1.25 veces; `entra` desde 1.25 veces. Si no hay GPU, se muestra el estado de CPU y se deshabilita instalar solo cuando `cpu` es falso. El espacio usado suma archivos regulares sin seguir enlaces; el libre se consulta en la ruta existente más cercana. Se calcula al consultar `/storage`. La confirmación de traslado muestra una estimación orientativa a 50 MB/s a partir del espacio usado; no retrasa ni condiciona el trabajo.
- **Descartadas**: un umbral binario no representa el estado intermedio pedido; crear carpetas durante una lectura modificaría el disco; recorrer enlaces podría incluir datos fuera de las raíces elegidas; una estimación basada en el hardware concreto no está disponible sin medir cada disco.
- **Cómo revertir**: ajustar `vramLabel`, el cálculo de estimación y las funciones de métricas en `storage.py`, y actualizar sus pruebas.
- **Cómo comprobarla**: pruebas de los límites de VRAM y de `/storage` con carpetas aisladas, archivos y enlaces.
- **Pendiente**: ninguna.
- **Actualización de caché**: al finalizar o fallar un trabajo `engine.*` por SSE, se invalidan Motores y el catálogo de narración; `storage.move` invalida Almacenamiento. Así la UI vuelve a consultar el estado que confirmó el worker. El asistente muestra la ruta de destino como encolada, no como traslado completado.
- **Carga y auditoría**: `engines.group.*` se declara como prefijo dinámico porque los nombres se seleccionan desde `GROUPS`; `engines.size.*` cubre la etiqueta de tamaño condicional. Motores, Ajustes y bienvenida se cargan bajo demanda; el selector de carpetas importa su diálogo al abrirlo para preservar el bundle inicial.

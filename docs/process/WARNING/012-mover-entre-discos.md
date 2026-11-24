# 012: reubicación con copia verificada entre volúmenes

- **Contexto**. Un cambio de volumen requiere copiar los archivos antes de publicar la ruta nueva. Las rutas históricas ya están en la base y en los proyectos.
- **Elegida**. En el mismo volumen se renombra y se restauran las rutas editables si falla el guardado. En otro volumen se verifica el tamaño y el SHA-256 antes de reescribir las rutas en la copia y guardar las preferencias. La cola espera a que terminen los trabajos activos y conserva el turno hasta que el traslado termina. Los enlaces históricos de archivos se resuelven con el mapa guardado en SQLite.
- **Descartadas**. Actualizar las preferencias antes de la copia dejaría los trabajos sin una carpeta completa ante un fallo. Reescribir cada trabajo duplicaría la actualización de rutas.
- **Cómo revertir**. Desde Almacenamiento, mueve la carpeta de vuelta a su ubicación anterior después de que termine el trabajo.
- **Cómo comprobarla**. Ejecuta el test espejo de `storage/relocate.py`, el de `storage_move.py` y los de API. La verificación final usa salidas de prueba entre volúmenes.

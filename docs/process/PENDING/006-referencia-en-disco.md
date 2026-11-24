# 006: regenerar relee el audio de referencia del disco en cada petición

- **Qué**: cada regeneración vuelve a leer del disco el audio de referencia de la voz. El resultado es el mismo; cuesta tiempo en cada párrafo regenerado.
- **Por qué no se hizo**: la caché de medios va en memoria ([WARNING 006-media-cache](../WARNING/006-media-cache.md)) y no cubre la referencia. Cachearla exige decidir cuándo se invalida, por si el usuario cambia el archivo de voz. Fuera de alcance de 006.
- **Cuándo**: después de cerrar la 006, junto con la caché de medios.
- **Quién**: agente.
- **Qué la cierra**: una caché de la referencia por ruta, fecha de modificación y tamaño, como la de `/media`, y una prueba que cuente las lecturas.

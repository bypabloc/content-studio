# 023: quemar los subtítulos antes de convertir a vertical los corta

- **Qué**: el recorrido de la spec (paso 7 quemar, paso 8 convertir a Reels) deja los subtítulos cortados a izquierda y derecha: el encuadre vertical recorta un video horizontal que ya los tiene quemados. En el orden inverso (convertir, editar y quemar al final, como quedó el video final de la 023) salen completos.
- **Por qué no se hizo**: es una guía de uso o un aviso, no un fallo de un módulo.
- **Cuándo**: con la próxima spec de Convertir o de Subtítulos.
- **Quién**: agente.
- **Qué la cierra**: un aviso en Convertir a Redes cuando el origen es una salida de `subtitles.burn`, o el paso «convertir a vertical» dentro de la quema.

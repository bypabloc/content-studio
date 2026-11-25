# 026: chatterbox: aviso de LUFS del mastering y mapa Cangjie que no carga

- **Qué**: en la salida de prueba, el mastering avisa `-16.6 LUFS (target -16.0)` y el tokenizador no carga el mapa Cangjie (la ruta se duplica dentro de la caché de HF: `snapshots/<sha>/models--ResembleAI--chatterbox/snapshots/<sha>`). El texto en español no usa ese mapa.
- **Por qué no se hizo**: el mastering es de la narración y la ruta duplicada viene del código de chatterbox; fuera del alcance de la spec 026.
- **Cuándo**: antes de publicar.
- **Quién**: usuario (escucha) y agente (revisar el ajuste de mastering).
- **Qué la cierra**: medición del volumen con la tolerancia del README y un aviso del mastering que no aparezca, o una decisión registrada.

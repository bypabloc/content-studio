# 026: heartmula en Python 3.14 o más cuando torchtune deje datasets 2.14.4

- **Qué**: subir heartmula a 3.14 cuando torchtune o heartlib dejen de fijar `datasets` 2.14.4 o de exigir `torch<2.11`, y repetir la verificación.
- **Por qué no se hizo**: torchtune 0.4.0 (pinado por heartlib) fija `datasets==2.14.4`, incompatible con pyarrow 21 o más nueva.
- **Cuándo**: después de publicar, o al salir una heartlib nueva.
- **Quién**: agente.
- **Qué la cierra**: instalación de heartmula en la versión nueva con su import de heartlib y una pista corta generada.

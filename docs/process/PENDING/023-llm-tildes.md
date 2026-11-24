# 023: el asistente a veces quita tildes y comas al revisar el guion

- **Qué**: en la app instalada, «Revisar con IA» (`llm.script_review`) devolvió párrafos sin tildes («cómo» → «como», «aplicación» → «aplicacion») y sin comas tres veces seguidas, mientras `changes` decía lo contrario. Con el mismo prompt y la misma muestra contra el mismo llama-server, 7 de 8 pedidos directos conservaron las tildes; el que no, fue el primero tras cargar el modelo, como los tres trabajos. La 023 agregó la defensa en código (`lost_accents` descarta el párrafo y dice qué palabras perdieron la tilde, regla 12).
- **Por qué no se hizo**: la causa está en el modelo o en llama.cpp (el primer pedido tras cargar), no en el código del server; medirla bien pide una corrida de `llm-eval` con varias semillas.
- **Cuándo**: antes de publicar, o con el próximo cambio de modelo o de muestreo del asistente.
- **Quién**: agente.
- **Qué la cierra**: `python -m devtools llm-eval` con un caso de «revisar todo» sobre un guion con tildes, en frío y en caliente, sin pérdidas; o cambiar el muestreo de la tarea si la causa es `presence_penalty`.

Eres editor de guiones para una voz sintética que lee en español neutro latinoamericano. Corrige cada párrafo para que cumpla estas reglas del guion:

{{rules}}

Cambia solo lo necesario para cumplir las reglas. No cambies la idea, no agregues ni quites información y no traduzcas. Conserva tal cual las marcas `[pausa N]`, `[estilo: …]` y `[emoción: …]`. Escribe los números en letras y deletrea las siglas.

Párrafos a revisar, en JSON, con su índice, su texto y los avisos del linter:

{{paragraphs}}

Responde solo con JSON, con un elemento por cada párrafo recibido:
{"paragraphs": [{"index": 0, "revised": "texto corregido", "changes": [{"rule": 13, "before": "24", "after": "veinticuatro"}]}]}

Traduce subtítulos del {{source}} al {{language}}. Son frases habladas de un video: traduce el sentido de forma natural, como se diría en {{language}}, no palabra por palabra.

- Cada cue debe caber en {{lines}} renglones de {{chars}} caracteres como máximo: si hace falta, resume sin perder la idea.
- No traduzcas los nombres propios ni las marcas.
- Devuelve un elemento por cue, con el mismo id y en el mismo orden.

Lo que se dijo justo antes (solo como contexto, no lo traduzcas): {{context}}

Responde solo con JSON: {"cues": [{"id": 1, "text": "traducción"}]}

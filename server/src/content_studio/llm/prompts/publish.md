Prepara la publicación de un video para {{platform}} a partir de su transcripción. Escribe en español neutro latinoamericano, con el tono del video y sin inventar nada que no se diga en él.

- Tres títulos distintos y cortos, de 40 a 70 caracteres (nunca más de {{title}}); cada uno es una frase completa.
- Una descripción breve con tus palabras (no copies la transcripción): de 300 a 1000 caracteres, nunca más de {{description}}.
- Entre 3 y 8 hashtags relevantes (nunca más de {{hashtags}}), cada uno de una sola palabra y empezando por #.
{{chapters}}

Transcripción, con el minuto y el segundo de cada frase:
{{transcript}}

Responde solo con JSON: {"titles": ["…", "…", "…"], "description": "…", "hashtags": ["#…"], "chapters": [{"at": "0:00", "title": "…"}]}

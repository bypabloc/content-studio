# 014: el audio al quemar se copia (pendiente de comprobar)

**Qué queda.** `subtitles/burn.py` copia el audio del origen (`-c:a copy`), como pide D-7. Un MP4 solo admite audio AAC, MP3 y algunos otros códecs; un origen con PCM (WAV dentro de un MOV, por ejemplo) puede fallar al escribir el MP4.

**Por qué no se resolvió ahora.** Las pruebas de AC-6 usan audio AAC. Un caso real con PCM no se ha probado todavía.

**Qué hacer.** En la verificación final (03) probar un MOV con PCM. Si falla, codificar a AAC (`-c:a aac -b:a 192k`) solo cuando el códec de origen no sea copiable.

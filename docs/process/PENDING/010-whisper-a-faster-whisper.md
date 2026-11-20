# 010: el chequeo y la evaluación de tomas usan openai-whisper; la 013 pasa a faster-whisper

- **Qué**: el chequeo de una toma y la evaluación de la narración usan `openai-whisper` (el comando `whisper`). La spec 013 trae faster-whisper.
- **Por qué no se hizo**: cambiar el motor de whisper es de la 013, según la decisión de la spec 01 (`01-contexto-y-decision.md`).
- **Cuándo**: en la 013.
- **Quién**: agente.
- **Qué lo cierra**: la 013 cambia el motor de whisper del chequeo y de la evaluación a faster-whisper, con su prueba.

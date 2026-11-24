# 013: la receta de CosyVoice sigue instalando openai-whisper

- **Qué**: la receta `server/src/content_studio/engines/recipes/cosyvoice3.json` instala `openai-whisper==20250625`. Desde la 013, nada del código lo usa como comando (`whisper`), pero no se comprobó si CosyVoice lo importa en su propio código.
- **Por qué no se hizo**: D-7 dice que se quita de la receta solo si deja de hacer falta. Quitarlo cambia la instalación de un motor, y no se puede verificar sin instalar CosyVoice.
- **Cuándo**: después de la 013, antes de la próxima instalación limpia de CosyVoice.
- **Quién**: agente.
- **Qué la cierra**: buscar `whisper` en el código de CosyVoice (`engines/CosyVoice`). Si no se importa, quitarlo de la receta y reinstalar el motor para probarlo.

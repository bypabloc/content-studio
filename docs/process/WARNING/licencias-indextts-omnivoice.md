# IndexTTS y OmniVoice no se pueden verificar sin aceptar su licencia

- **Contexto**: IndexTTS (bilibili Model Use License) y OmniVoice (CC-BY-NC) no son de uso comercial. Su receta está fijada (IndexTTS en Python 3.11, OmniVoice en 3.14), pero ninguno se instaló ni generó audio en la verificación de la 026, porque la instalación pide aceptar la licencia.
- **Elegida**: dejarlos sin verificar hasta que el usuario decida.
- **Descartadas**: aceptar la licencia en nombre del usuario.
- **Cómo revertir**: no aplica.
- **Cómo comprobarla**: el usuario acepta la licencia en Motores (o decide no usar esos motores). Después, el agente instala cada uno y genera una salida corta con `uv run studio narration tts --model <motor> ...`, midiendo la duración y el LUFS.

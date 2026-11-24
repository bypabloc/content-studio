# 021: `studio narration tts --file guion.txt` sin `--style` falla con «No existe el estilo None»

- **Qué**: la ayuda dice que, sin `--style`, se usa el `style` del JSON o `expert`; con un `.txt` el trabajo sale con exit 2 y «No existe el estilo None». Con `--style expert` funciona. Visto el 24/11/2026 en la verificación de la 021; el código de narración no cambió en esa rama.
- **Por qué no se hizo**: es de la narración (specs 004 y 006), fuera del alcance del asistente.
- **Cuándo**: antes de publicar.
- **Quién**: agente.
- **Qué la cierra**: una prueba en `server/tests/test_bugs.py` con un `.txt` sin `--style` y el valor por defecto en `services/narration.py` o en el parser.

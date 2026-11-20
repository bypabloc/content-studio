# 010: kit de grabación y tomas (ciclo 2)

- **Contexto**: D-3 y D-6 piden el kit (orden, duración, ppm y guion por estilo) y las tomas por perfil, con elegir una. La spec no fija el nombre del módulo de tomas ni cómo viaja el WAV en la subida.
- **Elegida**:
  - Las tomas de perfil van en `narration/profile_takes.py`, con sus tests en `test_profile_takes.py`, y AC-5 se verifica ahí. `narration/takes.py` ya existe y es de la 006 (`regenerate_take`, tomas de narración): reutilizar ese nombre mezclaría las tomas de regenerar con las de perfil.
  - La toma se sube como cuerpo binario (`POST .../takes/{style}` con el WAV crudo), no como multipart: `python-multipart` no es dependencia del server y no se agrega una para un solo endpoint.
  - `recording_kit.py` guarda orden, duración y ppm como datos. Los ppm son los de docs/scripts/README.md; whisper, que es opcional, no tiene ppm.
  - El texto exacto sale de la sección «Texto exacto» de cada guion, que es lo que se graba y se compara. La versión marcada sale de «Versión marcada» y es la del teleprompter. El texto no se copia al código: la prueba compara cada estilo con su `.txt` versionado.
  - `choose` copia la toma a `<estilo>.wav` (la toma queda en `takes/`), escribe el texto exacto como `<estilo>.txt` y pasa la referencia reemplazada a `takes/` con el siguiente número.
  - `styles_status` vive en `profiles.py`, junto a `takes_dir` y `take_numbers`: así `profile_takes` depende de `profiles` y no al revés.
  - El estado del chequeo (`check.json`) no existe todavía. Llega con `voice.check` en el ciclo 3.
- **Descartadas**:
  - Un `takes.py` nuevo que reemplace al de regenerar: mezclaría dos conceptos y obligaría a tocar la 006.
  - Multipart: habría agregado una dependencia para un solo endpoint.
- **Cómo revertir**: revertir el commit `feat: kit de grabación y tomas por estilo en la API`. Los perfiles y el paso 3 del ciclo 1 siguen.

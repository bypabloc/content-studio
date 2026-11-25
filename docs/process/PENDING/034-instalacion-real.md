# 034: instalación real de pyannote con el token del usuario

- **Qué**: la verificación final de la 034 pide instalar `pyannote` con el token de Hugging Face del usuario y revisar `install.json`, `models/community-1/config.yaml`, que `verify` importe `pyannote.audio` y que ningún log tenga el token. No se hizo porque el token es del usuario (`blocked — user-credential`). El paso `hf` sí se comprobó con un token falso: Hugging Face niega el acceso y el paso sale con 25.
- **Cómo cerrarlo**: el usuario acepta las condiciones en https://huggingface.co/pyannote/speaker-diarization-community-1, crea un token de lectura y lo pega en Motores > Diarización. Después se instala `pyannote` y se revisan `install.json`, `rg -n "hf_" logs/jobs/<id>.log` y el resultado de `verify`.
- **Cuándo**: antes de la corrida real de la 035, que también la necesita.

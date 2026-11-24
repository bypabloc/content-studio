# 022: la descarga de Hugging Face falla con una carpeta de datos muy profunda

- **Qué**: en la verificación, con `CONTENT_STUDIO_HOME` en `…\022-installer\tmp\app-check\<run>\home` (unos 100 caracteres), `engines install qwen-0.6b` falló al 83 %: el symlink de `huggingface_hub` en `engines\hf\qwen-0.6b\hub\models--Qwen--…\snapshots\<rev>\speech_tokenizer\preprocessor_config.json` pasa los 260 caracteres de `MAX_PATH` (`WinError 3`). Con una carpeta corta pasó. La ruta por defecto (`%LOCALAPPDATA%\Content Studio`) deja unos 70 caracteres de margen; una carpeta de motores elegida en Ajustes > Almacenamiento más profunda daría el mismo error.
- **Por qué no se hizo**: fuera del alcance de la 022 (el instalador); la descarga es de los motores (spec 009).
- **Cuándo**: después del lote, o antes si alguien elige una carpeta de motores profunda.
- **Quién**: agente.
- **Qué la cierra**: un aviso en Ajustes > Almacenamiento si la carpeta deja menos margen que el más largo de los repos, o la descarga con `HF_HUB_DISABLE_SYMLINKS=1`, y una prueba en `server/tests/unit/src/content_studio/engines/`.

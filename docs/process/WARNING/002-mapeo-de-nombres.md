# 002: mapeo de nombres de español a inglés (ciclos 4 y 5)

- **Contexto**: la 002 traduce el código y los datos a inglés (D-7). El pase de renombrado (`git mv` de módulos y tokens NAME/STRING de identificadores) se aplicó a todo `server/src/content_studio/**`, `server/tests/**` y `cli.py`. El pase no toca docstrings ni comentarios, así que sigue en español. Hubo que corregir a mano: `LETRA` de `compare.py` (letras del alfabeto) se había traducido como `lyrics` (`LETTERS` ahora); `en_words` (en palabras) se renombró como `as_words`; los nombres `guardar*` y `corte` no estaban en la tabla; y los valores de modo y las claves de metadatos (`clonacion`, `parametros`, `fecha`, `observaciones`…) quedaron a medias.
- **Elegida**: traducción por paquete según D-7, con una tabla de partes en `scratchpad/renombrar.py`. Los mensajes y logs pasan a inglés (fuera de alcance: el catálogo de mensajes en español lo hace la 004). Los docstrings y comentarios siguen en español. Los renombres se hicieron en el mismo commit que sus fixtures, porque el pre-commit corre pytest.
- **Descartadas**:
  - Renombrar `aprobacion.json` a `approval.json`: `narration/voices/catalog.py` decide si una voz está aprobada por ese archivo; cambiarlo dejaría sin aprobar todas las voces construidas sin una migración. Se queda (ver PENDING `002-nombres-en-disco`).
  - Poner palabras en español en `devtools/cspell/content-studio-terms.txt`: prohibido por D-1. Solo entran nombres propios de motores, voces y datasets, y términos técnicos en inglés.
  - Usar `language: en,es` para el catálogo de voces: el diccionario es-es no trae palabras como `motivacional` o `licenciante`. El catálogo queda en `ignorePaths` (ver PENDING `002-cspell-excepciones-temporales`).
- **Desvíos del plan** (`02-plan.md`):
  - Ciclo 4 incluye renombres mecánicos de `cli/` (`comandos`→`commands`, `flujo`→`flow`, `ayuda`→`help_text`), de `music/` y de `grabar/`, porque el pase cubre todo `server/src`. Los mensajes de `cli/` y `grabar/` siguen en español y excluidos de cspell.
  - Las fixtures de caracterización se regeneran en el commit del ciclo 4, no en el ciclo 7: pre-commit corre pytest y cada commit tiene que pasar.
  - Los temporales de `base-cruda.wav` y `.crudo.wav` pasan a `base-raw.wav` y `.raw.wav`: son archivos intermedios que el código regenera, no estado de voces.
- **Cómo revertir**: `git revert` del commit del ciclo 4. Los `git mv` son parte de ese mismo commit.
- **Cómo comprobarla**: `uv run pytest -q` (334 pasan) y `uv run python -m devtools spelling`. Solo quedan fuera de alcance `.github/`, `.git-hooks/pre-push`, `.claude/mods/` y `server/pyproject.toml`, que son de los ciclos 6 y 8.
- **Pendiente**: [002-cspell-excepciones-temporales](../PENDING/002-cspell-excepciones-temporales.md) y [002-nombres-en-disco](../PENDING/002-nombres-en-disco.md).

## Mapeo de módulos (paquete `content_studio`)

| Antes | Después |
| :--- | :--- |
| `rutas.py` | `paths.py` (`RAIZ`→`ROOT`, `VOZ`→`REFERENCE`, `VOCES`→`VOICES`, `TOMAS`→`TAKES`) |
| `comun/` | `common/`: `proceso.py`→`process.py`, `archivos.py`→`files.py`, `ffmpeg.py` igual |
| `cli/comandos/` | `cli/commands/` · `cli/flujo.py`→`cli/flow.py` · `cli/ayuda.py`→`cli/help_text.py` |
| `music/estilos.py` | `music/styles.py` · `music/musica.py`→`music/music_main.py` · `music/evaluacion.py`→`music/evaluation.py` |
| `music/motores/` | `music/engines/` · `registro.py`→`registry.py` (`EspecMusica`→`MusicSpec`, `MotorMusica`→`MusicEngine`, `MODELOS`→`MODELS`) |
| `narration/motores/` | `narration/engines/` · `registro.py`→`registry.py` (`EspecMotor`→`EngineSpec`, `MotorTTS`→`TTSEngine`, `MOTORES`→`ENGINES`) |
| `narration/estilos.py` | `narration/styles.py` · `guion.py`→`script.py` · `bloques.py`→`blocks.py` |
| `narration/metadatos.py` | `narration/metadata.py` · `referencia.py`→`reference.py` |
| `narration/texto/` | `narration/text/`: `segmentos.py`→`segments.py`, `traducir.py`→`translate.py` |
| `narration/evaluacion/` | `narration/evaluation/`: `comparar.py`→`compare.py`, `revisar.py`→`review.py` |
| `narration/voces/` | `narration/voices/`: `construir.py`→`build.py`, `catalogo.py`→`catalog.py`, `fuentes.py`→`sources.py` |
| `tests/test_asistente.py` … | `test_assistant.py`, `test_characterization.py`, `test_registry.py`, `fixtures/generate.py` |

## Mapeo de datos (`server/data/`, con `git mv` para lo versionado)

| Antes | Después |
| :--- | :--- |
| `narration/voz/<estilo>.txt` | `narration/reference/<style>.txt` (tabla de estilos abajo) |
| `narration/voz/tomas/` | `narration/reference/takes/` (move-data, T9) |
| `narration/voces/`, `voces/catalogo.json` | `narration/voices/`, `voices/catalog.json` |
| `narration/motores/` | `narration/engines/` (move-data, T9) |
| `narration/docs/guiones/` | `narration/docs/scripts/` |

Estilos: `amistosa→friendly`, `suave→soft`, `experta→expert`, `clara→clear`, `estable→steady`, `energica→energetic`, `dramatica→dramatic`, `triste→sad`, `intima→intimate`, `susurro→whisper`, `neutral-fin→neutral-end`. Emociones: `alegre→happy`, `enojado→angry`, `miedo→fear`, `sorpresa→surprise`, `calma→calm`, `urgente→urgent`. Las claves de `catalog.json` y los nombres de voces no cambian.

## Valores y claves que cambian en la salida

| Antes | Después | Dónde |
| :--- | :--- | :--- |
| `texto`, `estilo`, `emocion`, `pausa`, `segmentos` | `text`, `style`, `emotion`, `pause`, `segments` | JSON de guion y fixtures |
| `[pausa N]`, `"texto"` | siguen funcionando; alias en `narration/script_aliases.json` | parser del guion (AC-5) |
| `clonacion`, `controlable`, `parametros` (modo) | `cloning`, `controllable`, `params` | `engines/` |
| `text_enviado`, `pause_despues`, `fecha`, `time_generacion_s`, `observaciones` | `text_sent`, `pause_after`, `date`, `time_generation_s`, `observations` | metadatos `.json` de cada salida |
| `--build todas` | `--build all` | `narration voices` |
| `lufs_objetivo` | `target_lufs` | metadatos |

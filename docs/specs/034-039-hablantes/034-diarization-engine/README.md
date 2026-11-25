# Spec 034: Motor de diarización `pyannote` con token de Hugging Face

> **Decisiones y pendientes al ejecutar**: quien implemente esta spec puede tomar **todas las decisiones técnicas** que necesite, sin detenerse a pedir confirmación.
> Cada una queda anotada en [`docs/process/WARNING/`](../../../process/WARNING/README.md) (ficha `034-<tema>.md` con contexto, elegida, descartadas, cómo revertir y cómo comprobarla, y su fila en el README de la carpeta).
> Toda revisión pendiente queda en [`docs/process/PENDING/`](../../../process/PENDING/README.md) (ficha y fila, con qué la cierra).
>
> **Datos del usuario: solo los que crea esta spec**. La spec no borra ni sobrescribe voces grabadas (`server/data/narration/voz/`), voces construidas, salidas de `out/` ni modelos descargados que ella no creó. Sus pruebas escriben en carpetas nuevas (`out/<herramienta>/spec-034/` o `tmp/spec-034/`). Si algo parece exigir tocar datos existentes, no se decide al ejecutar: es un `blocked — user-data` y se pregunta. Los cambios locales o sin rastrear del checkout principal no son de la spec: no se tocan y no bloquean.

| Campo | Valor |
| :--- | :--- |
| Tipo | feature |
| Escala | Large (11+ archivos) |
| Rama | `feature/034-diarization-engine` desde `origin/dev`, en `../content-studio-worktrees/034-diarization-engine/` |
| Depende de | nada (ver «Relación con el lote 025–033» en el [README del lote](../README.md)) |
| Origen | Pedido del usuario (2026-11-24) · [investigación](../../../research/diarizacion-pyannote/README.md) |

## Objetivo

Instalar desde Motores el motor «Diarización (pyannote)»:

* con su receta fijada;
* con el token de Hugging Face del usuario, guardado en la base y nunca devuelto por la API;
* con errores claros si el usuario no tiene acceso al repositorio restringido.

## Cuándo leer cada archivo

| Archivo | Qué trae | Cuándo leer |
| :--- | :--- | :--- |
| [01-contexto-y-decision.md](01-contexto-y-decision.md) | Precondición, hallazgos, decisiones, fuera de alcance y AC | Primero |
| [02-diseno.md](02-diseno.md) | Receta, credenciales, API, errores y textos | Antes de la primera fase |
| [fases/1-receta-y-token/](fases/1-receta-y-token/plan-tdd.md) | Receta, familia, token en la instalación y repositorio restringido | Fase 1 |
| [fases/2-credenciales/](fases/2-credenciales/plan-tdd.md) | Almacén del token y API | Fase 2 |
| [fases/3-client/](fases/3-client/plan-tdd.md) | Tarjeta del motor, campo del token y atribución | Fase 3 |
| [03-verificacion-final.md](03-verificacion-final.md) | Batería, instalación real, cierre y PR | Con todos los commits hechos |

## Estado por fase

| Fase | Qué | Ciclos | AC | Commit | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F0 | Ajustes a la 026: receta en Python 3.14 (commit docs) | - | - | c16d7ec | IMP |
| F1 | [Receta, familia y token en la instalación](fases/1-receta-y-token/plan-tdd.md) | C1, C2, C3 | AC-1, AC-2, AC-3 | 5f563b9 | IMP |
| F2 | [Credenciales y API](fases/2-credenciales/plan-tdd.md) | C4, C5 | AC-3, AC-4 | - | IMP |
| F3 | [Client: tarjeta, token y atribución](fases/3-client/plan-tdd.md) | C6 | AC-5, AC-6 | - | PEN |
| FV | [Verificación final](03-verificacion-final.md) | - | todos | - | PEN |

## Decisiones cerradas (no reabrir)

1. **D-1**: Los pesos se obtienen con el token del usuario, no con un espejo propio (usuario, 2026-11-24).
2. **D-2**: El token se guarda en `settings` con la clave `secret.huggingface.token`. `GET/PUT /settings/secret.*` responden 403 y solo `/credentials/huggingface` lo escribe o lo borra; nunca lo devuelve (agente, 2026-11-24).
3. **D-3**: El token llega al paso `hf` solo en la variable de entorno `HF_TOKEN`, y solo si el paso declara `"gated": true`. Nunca va en `argv`, en el JSON del paso ni en el log (agente, 2026-11-24).
4. **D-4**: Hay dos errores nuevos:
   * `engine_token_required` (409): se responde antes de encolar, si el motor está restringido y no hay token;
   * `engine_gated` (exit 25): cuando Hugging Face responde 401 o 403.

   Los dos llevan un texto que explica cómo aceptar las condiciones (agente, 2026-11-24).
5. **D-5**: La receta `pyannote` queda así (agente, 2026-11-24):
   * Python 3.14, con torch y torchaudio `2.11.0+cu128`, igual que `qwen-0.6b` (fase `0-ajustes`: la 026 lleva cada receta a la Python más alta que soporta);
   * `pyannote.audio==4.1.1`, `torchcodec==0.17.0` y `huggingface-hub==0.36.2`;
   * los pesos de `pyannote/speaker-diarization-community-1` en la revisión `3533c8cf8e369892e6b79ff1bf80f7b0286a54ee`, descargados a `models/community-1`.
6. **D-6**: La familia nueva es `diarization`, con su grupo «Diarización» en Motores. La atribución CC-BY-4.0 va en la tarjeta y en Ajustes > Acerca de (agente, 2026-11-24).

## Reglas críticas

- El token no aparece en respuestas de la API, logs, `params.json`, `install.json` ni mensajes de error. Un test lo comprueba en cada superficie.
- La receta fija versiones con `==` y la revisión con un SHA (`test_recipes.py`).
- Dos capas: `huggingface_hub` se importa dentro de funciones y corre en el venv del motor.
- Textos visibles en los tres catálogos; los mensajes de logs y CLI, en inglés.
- Cada `.py` de fuente en 300 líneas o menos; tests en 800.

## Matriz de verificación

| AC | Fase | Ciclo | Test | Verificación real |
| :--- | :--- | :--- | :--- | :--- |
| AC-1 | F1 | C1 | `server/tests/unit/src/content_studio/engines/test_recipes.py::test_ac1_pyannote_recipe` | solo pytest |
| AC-2 | F1 | C2 | `server/tests/unit/src/content_studio/engines/test_steps.py::test_ac2_token_en_env_no_en_argv` | instalación real (FV) |
| AC-3 | F1 | C3 | `server/tests/unit/src/content_studio/engines/test_steps.py::test_ac3_gated_repo_exits_25` | solo pytest |
| AC-3 | F2 | C5 | `server/tests/unit/src/content_studio/api/routes/test_engines.py::test_ac3_without_token_returns_409` | solo pytest |
| AC-4 | F2 | C4 | `server/tests/unit/src/content_studio/api/routes/test_credentials.py::test_ac4_never_returns_the_token` | solo pytest |
| AC-5 | F3 | C6 | `client/tests/unit/src/features/engines/HfTokenField.test.tsx` y `tests/e2e/engines/happy-hf-token.e2e.ts` | e2e, app-check |
| AC-6 | F3 | C6 | `client/tests/unit/src/features/settings/About.test.tsx` | app-check |

## WARNING y PENDING

- WARNING: `034-token-en-settings` (D-2), `034-receta-pyannote` (D-5).
- PENDING: `034-instalacion-real`, solo si falta el token del usuario en la FV (`blocked — user-credential`).

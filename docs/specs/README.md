# Specs (planes de implementación)

Planes efímeros: cada spec vive aquí mientras se implementa y su último commit borra la carpeta y su fila. Formato: [`.agents/rules/plan-format.md`](../../.agents/rules/plan-format.md). Plantilla: [`_plantilla/`](_plantilla/README.md) (`cp -r docs/specs/_plantilla docs/specs/<NN>-<slug>`; no lleva fila en esta tabla). Redactar: skill `crear-spec`; implementar: `execute-spec`; varias en secuencia: `run-specs`.

El estado del proyecto y lo ya implementado viven en [`docs/process/`](../process/README.md).

| Spec | Tipo | Escala | Rama | Estado |
| :--- | :--- | :--- | :--- | :--- |
| [001-017-studio](001-017-studio/README.md) (lote 001–023) | refactor · feature | Large | una por spec | las 23 redactadas, PEN |
| ↳ [012-engines-storage](001-017-studio/012-engines-storage/README.md) | feature | Large | `feature/012-engines-storage` | PEN |
| ↳ [013-whisper-cleaner](001-017-studio/013-whisper-cleaner/README.md) | feature | Large | `feature/013-whisper-cleaner` | PEN |
| ↳ [014-subtitles](001-017-studio/014-subtitles/README.md) | feature | Large | `feature/014-subtitles` | PEN |
| ↳ [015-convert-normalize-trim](001-017-studio/015-convert-normalize-trim/README.md) | feature | Large | `feature/015-convert-normalize-trim` | PEN |
| ↳ [016-mix-ducking](001-017-studio/016-mix-ducking/README.md) | feature | Medium | `feature/016-mix-ducking` | PEN |
| ↳ [017-editor-core](001-017-studio/017-editor-core/README.md) | feature | Large | `feature/017-editor-core` | PEN |
| ↳ [018-editor-visual](001-017-studio/018-editor-visual/README.md) | feature | Large | `feature/018-editor-visual` | PEN |
| ↳ [019-editor-effects](001-017-studio/019-editor-effects/README.md) | feature | Large | `feature/019-editor-effects` | PEN |
| ↳ [020-library](001-017-studio/020-library/README.md) | feature | Large | `feature/020-library` | PEN |
| ↳ [021-local-llm-assist](001-017-studio/021-local-llm-assist/README.md) | feature | Large | `feature/021-local-llm-assist` | PEN |
| ↳ [022-installer](001-017-studio/022-installer/README.md) | feature | Large | `feature/022-installer` | PEN |
| ↳ [023-integral-verification](001-017-studio/023-integral-verification/README.md) | chore | Micro | `chore/023-integral-verification` | PEN |
| [024-app-check](024-app-check/README.md) | feature | Large | `feature/024-app-check` | PEN |

El próximo número libre es **025**. Los números no se reutilizan: una spec cerrada deja su número en el historial de git.

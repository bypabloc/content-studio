# Specs (planes de implementación)

Planes efímeros: cada spec vive aquí mientras se implementa y su último commit borra la carpeta y su fila. Formato: [`.agents/rules/plan-format.md`](../../.agents/rules/plan-format.md). Plantillas: [`_plantilla/`](_plantilla/README.md). Redactar: skill `crear-spec`; implementar: `execute-spec`; varias en secuencia: `run-specs`.

El estado del proyecto y lo ya implementado viven en [`docs/process/`](../process/README.md).

| Spec | Tipo | Escala | Rama | Estado |
| :--- | :--- | :--- | :--- | :--- |
| [001-017-studio](001-017-studio/README.md) (lote 001–021) | refactor · feature | Large | una por spec | las 21 redactadas, PEN |
| ↳ [003-test-runner](001-017-studio/003-test-runner/README.md) | chore | Large | `chore/003-test-runner` | PEN |
| ↳ [006-narration-section](001-017-studio/006-narration-section/README.md) | feature | Large | `feature/006-narration-section` | PEN |
| ↳ [007-icons](001-017-studio/007-icons/README.md) | feature | Medium | `feature/007-icons` | PEN |
| ↳ [008-voices-recording](001-017-studio/008-voices-recording/README.md) | feature | Large | `feature/008-voices-recording` | PEN |
| ↳ [009-music-section](001-017-studio/009-music-section/README.md) | feature | Large | `feature/009-music-section` | PEN |
| ↳ [010-engines-storage](001-017-studio/010-engines-storage/README.md) | feature | Large | `feature/010-engines-storage` | PEN |
| ↳ [011-whisper-cleaner](001-017-studio/011-whisper-cleaner/README.md) | feature | Large | `feature/011-whisper-cleaner` | PEN |
| ↳ [012-subtitles](001-017-studio/012-subtitles/README.md) | feature | Large | `feature/012-subtitles` | PEN |
| ↳ [013-convert-normalize-trim](001-017-studio/013-convert-normalize-trim/README.md) | feature | Large | `feature/013-convert-normalize-trim` | PEN |
| ↳ [014-mix-ducking](001-017-studio/014-mix-ducking/README.md) | feature | Medium | `feature/014-mix-ducking` | PEN |
| ↳ [015-editor-core](001-017-studio/015-editor-core/README.md) | feature | Large | `feature/015-editor-core` | PEN |
| ↳ [016-editor-visual](001-017-studio/016-editor-visual/README.md) | feature | Large | `feature/016-editor-visual` | PEN |
| ↳ [017-editor-effects](001-017-studio/017-editor-effects/README.md) | feature | Large | `feature/017-editor-effects` | PEN |
| ↳ [018-library](001-017-studio/018-library/README.md) | feature | Large | `feature/018-library` | PEN |
| ↳ [019-local-llm-assist](001-017-studio/019-local-llm-assist/README.md) | feature | Large | `feature/019-local-llm-assist` | PEN |
| ↳ [020-installer](001-017-studio/020-installer/README.md) | feature | Large | `feature/020-installer` | PEN |
| ↳ [021-integral-verification](001-017-studio/021-integral-verification/README.md) | chore | Micro | `chore/021-integral-verification` | PEN |

El próximo número libre es **022**. Los números no se reutilizan: una spec cerrada deja su número en el historial de git.

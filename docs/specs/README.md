# Specs (planes de implementación)

Planes efímeros: cada spec vive aquí mientras se implementa y su último commit borra la carpeta y su fila. Formato: [`.agents/rules/plan-format.md`](../../.agents/rules/plan-format.md). Plantillas: [`_plantilla/`](_plantilla/README.md). Redactar: skill `crear-spec`; implementar: `execute-spec`; varias en secuencia: `run-specs`.

El estado del proyecto y lo ya implementado viven en [`docs/process/`](../process/README.md).

| Spec | Tipo | Escala | Rama | Estado |
| :--- | :--- | :--- | :--- | :--- |
| [001-017-studio](001-017-studio/README.md) (lote) | refactor · feature | Large | una por spec | las 17 redactadas, PEN |
| ↳ [003-test-runner](001-017-studio/003-test-runner/README.md) | chore | Large | `chore/003-test-runner` | PEN |
| ↳ [006-narration-section](001-017-studio/006-narration-section/README.md) | feature | Large | `feature/006-narration-section` | PEN |
| ↳ [007-voices-recording](001-017-studio/007-voices-recording/README.md) | feature | Large | `feature/007-voices-recording` | PEN |
| ↳ [008-music-section](001-017-studio/008-music-section/README.md) | feature | Large | `feature/008-music-section` | PEN |
| ↳ [009-engines-storage](001-017-studio/009-engines-storage/README.md) | feature | Large | `feature/009-engines-storage` | PEN |
| ↳ [010-whisper-cleaner](001-017-studio/010-whisper-cleaner/README.md) | feature | Large | `feature/010-whisper-cleaner` | PEN |
| ↳ [011-subtitles](001-017-studio/011-subtitles/README.md) | feature | Large | `feature/011-subtitles` | PEN |
| ↳ [012-convert-normalize-trim](001-017-studio/012-convert-normalize-trim/README.md) | feature | Large | `feature/012-convert-normalize-trim` | PEN |
| ↳ [013-mix-ducking](001-017-studio/013-mix-ducking/README.md) | feature | Medium | `feature/013-mix-ducking` | PEN |
| ↳ [014-library](001-017-studio/014-library/README.md) | feature | Large | `feature/014-library` | PEN |
| ↳ [017-local-llm-assist](001-017-studio/017-local-llm-assist/README.md) | feature | Large | `feature/017-local-llm-assist` | PEN (se ejecuta antes de la 015) |
| ↳ [015-installer](001-017-studio/015-installer/README.md) | feature | Large | `feature/015-installer` | PEN |
| ↳ [016-integral-verification](001-017-studio/016-integral-verification/README.md) | chore | Micro | `chore/016-integral-verification` | PEN |

El próximo número libre es **018**. Los números no se reutilizan: una spec cerrada deja su número en el historial de git.

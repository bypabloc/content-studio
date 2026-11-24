"""Proceso de una tarea del asistente (spec 021, D-2): `python -m content_studio.llm.task_main <tarea> <carpeta>`.

Lee `params.json` de la carpeta del trabajo, habla con el llama-server que el worker dejó en `--url` y escribe
`result.json`. Un error del modelo sale con su código (EXIT_CODES) y el código en stderr.
"""

from __future__ import annotations

import argparse
import functools
import json
import sys
from pathlib import Path

from content_studio.common import progress
from content_studio.llm import client, models
from content_studio.llm.tasks import (
    music_caption,
    publish,
    script_review,
    subtitles_correct,
    subtitles_keywords,
    subtitles_translate,
)

TASKS = {
    'script_review': script_review,
    'music_caption': music_caption,
    'subtitles_translate': subtitles_translate,
    'subtitles_correct': subtitles_correct,
    'subtitles_keywords': subtitles_keywords,
    'publish': publish,
}
EXIT_CODES = {'llm_invalid_output': 30, 'llm_timeout': 31, 'llm_unavailable': 32, 'llm_not_installed': 33}


def main(argv: list[str] | None = None) -> int:
    """Corre la tarea y deja su resultado en la carpeta del trabajo."""
    ap = argparse.ArgumentParser(prog='task_main')
    ap.add_argument('task', choices=sorted(TASKS))
    ap.add_argument('out_dir', type=Path)
    ap.add_argument('--url', required=True)
    ap.add_argument('--model', required=True, choices=sorted(models.MODELS))
    args = ap.parse_args(argv)
    params = json.loads((args.out_dir / 'params.json').read_text(encoding='utf-8'))
    spec = models.MODELS[args.model]
    ask = functools.partial(client.chat, args.url, sampling=spec.sampling, extra=spec.extra)
    progress.emit(0.1, 'asking the assistant')
    try:
        result = TASKS[args.task].run(params, lambda messages, rule, check=None: ask(messages, rule, check=check))
    except client.LlmError as error:
        print(error.code, file=sys.stderr)
        return EXIT_CODES[error.code]
    (args.out_dir / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    finish = getattr(TASKS[args.task], 'finish', None)
    if finish is not None:  # publicar deja además publish.json y su ruta en la biblioteca
        finish(params, args.out_dir, result)
    progress.emit(1, 'done')
    return 0


if __name__ == '__main__':
    sys.exit(main())

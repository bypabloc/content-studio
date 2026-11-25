"""Catálogo de las herramientas MCP (spec 029, 02 §2): nombres, descripciones y esquemas.

Las descripciones van en inglés, porque las lee el modelo. Una herramienta nueva se agrega aquí y en el caso de AC-1
(la lista es cerrada).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

JOB_STATUSES = ('queued', 'running', 'waiting_gpu', 'done', 'error', 'cancelled')


@dataclass(frozen=True)
class ToolDef:
    """Una herramienta publicada: nombre, descripción (en inglés, para el modelo) y sus esquemas."""

    name: str
    title: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    read_only: bool = False
    destructive: bool = False


def _object(properties: dict[str, Any], required: tuple[str, ...] = ()) -> dict[str, Any]:
    return {'type': 'object', 'properties': properties, 'required': list(required)}


def _text(description: str) -> dict[str, Any]:
    return {'type': 'string', 'description': description}


PATH = _text('Path of an existing file on this computer. Prefer an absolute path.')
MODEL = _text('Engine name. studio_capabilities lists the installed ones.')
LANGUAGE = _text("Language of the speech, or 'auto'.")
JOB_ID = {'type': 'integer', 'description': 'Job id returned by a studio_* tool.'}

JOB_OUTPUT = _object(
    {
        'path': _text('Absolute path of the output file.'),
        'media': _text('audio, video or file.'),
        'duration_s': {
            'anyOf': [{'type': 'number'}, {'type': 'null'}],
            'description': 'Duration in seconds, when known.',
        },
    }
)
JOB = _object(
    {
        'job_id': {'type': 'integer'},
        'kind': _text('Job kind, such as narration or music.'),
        'status': {'type': 'string', 'enum': list(JOB_STATUSES)},
        'progress': {'type': 'number', 'description': 'From 0 to 1.'},
        'stage': {'anyOf': [{'type': 'string'}, {'type': 'null'}]},
        'waiting_on': {
            'anyOf': [{'type': 'string'}, {'type': 'null'}],
            'description': 'Who holds the GPU while status is waiting_gpu.',
        },
        'outputs': {'type': 'array', 'items': JOB_OUTPUT},
        'output_dir': {'anyOf': [{'type': 'string'}, {'type': 'null'}]},
        'error': {'anyOf': [{'type': 'object'}, {'type': 'null'}]},
        'timed_out': {'type': 'boolean', 'description': 'True when studio_wait_job stopped at timeout_s.'},
    }
)
GET_JOB = _object({'job': JOB, 'jobs': {'type': 'array', 'items': JOB}})
CAPABILITIES = _object(
    {
        'narration': {'type': 'object'},
        'music': {'type': 'object'},
        'conversion_targets': {'type': 'array', 'items': {'type': 'string'}},
        'job_kinds': {'type': 'array', 'items': {'type': 'string'}},
    }
)

TOOLS: tuple[ToolDef, ...] = (
    ToolDef(
        'studio_capabilities',
        'Capabilities',
        'List what content-studio can generate on this computer: installed narration '
        'and music engines, voices and styles, '
        'conversion targets, and the job kinds that studio_submit_job accepts. Call it first.',
        _object({}),
        CAPABILITIES,
        read_only=True,
    ),
    ToolDef(
        'studio_narrate',
        'Narrate text',
        'Narrate a text, or a .txt or .json script file, with a cloned voice, locally. Queues a narration job and '
        'returns it at once; call studio_wait_job to get the audio path.',
        _object(
            {
                'text': _text('Text to narrate.'),
                'script_path': PATH,
                'voice': _text('Voice name from studio_capabilities.'),
                'model': MODEL,
                'style': _text('Narration style, such as expert or happy. Default: expert.'),
            }
        ),
        JOB,
    ),
    ToolDef(
        'studio_make_music',
        'Make background music',
        'Generate instrumental background music (never vocals) from one or more style presets, '
        'locally. Queues a music job; wait with studio_wait_job.',
        _object(
            {
                'style': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Style presets, such as lofi-chill.',
                },
                'duration_s': {'type': 'number', 'description': 'Length in seconds.'},
                'model': MODEL,
            },
            ('style',),
        ),
        JOB,
    ),
    ToolDef(
        'studio_transcribe',
        'Transcribe media',
        'Transcribe an audio or video file to timed text, locally. Queues a job; when it '
        'is done, outputs lists the result files.',
        _object({'input_path': PATH, 'language': LANGUAGE, 'model': MODEL}, ('input_path',)),
        JOB,
    ),
    ToolDef(
        'studio_clean_silences',
        'Analyze silences',
        'Analyze an audio or video file for silences, so the cleaner can propose cuts. Queues an '
        'analysis job; the cuts are reviewed and applied in the app.',
        _object({'input_path': PATH, 'language': LANGUAGE}, ('input_path',)),
        JOB,
    ),
    ToolDef(
        'studio_convert_media',
        'Convert media',
        'Convert an audio or video file to another format or to a social-media preset, locally. Queues a '
        'job; the converted file is listed in outputs when done.',
        _object(
            {
                'input_path': PATH,
                'target': _text('Format or preset from studio_capabilities, such as mp3 or wav.'),
            },
            ('input_path', 'target'),
        ),
        JOB,
    ),
    ToolDef(
        'studio_submit_job',
        'Submit a job',
        'Queue any content-studio job kind with its params (the kinds come from studio_capabilities). '
        'Validation problems come back as isError with the list of errors.',
        _object(
            {
                'kind': _text('Job kind, such as narration or media.convert.'),
                'params': {
                    'type': 'object',
                    'description': 'Params of that kind, as studio_capabilities describes them.',
                },
            },
            ('kind',),
        ),
        JOB,
    ),
    ToolDef(
        'studio_get_job',
        'Get job status',
        'Get the status of a job by id, or the last 10 jobs when no id is given. A GPU job that waits '
        'for the GPU reports status waiting_gpu and who holds it.',
        _object({'job_id': JOB_ID}),
        GET_JOB,
        read_only=True,
    ),
    ToolDef(
        'studio_wait_job',
        'Wait for a job',
        'Wait until a job finishes or timeout_s passes (at most 300) and return its state '
        'and output files. Progress is reported while '
        'waiting. A timeout is not an error: the current state comes back with timed_out set.',
        _object(
            {
                'job_id': JOB_ID,
                'timeout_s': {
                    'type': 'integer',
                    'minimum': 0,
                    'maximum': 300,
                    'description': 'Seconds to wait. Default 60.',
                },
            },
            ('job_id',),
        ),
        JOB,
        read_only=True,
    ),
    ToolDef(
        'studio_cancel_job',
        'Cancel a job',
        'Cancel a queued or running job. Its process is terminated.',
        _object({'job_id': JOB_ID}, ('job_id',)),
        JOB,
        destructive=True,
    ),
    ToolDef(
        'studio_watch_folder',
        'Watch a folder',
        'Register a folder. Each file dropped in it is processed with the kind and params given, and its result is '
        'written to done/ or failed/ inside that folder.',
        _object(
            {
                'path': _text('Absolute path of an existing folder on this computer.'),
                'kind': {
                    'type': 'string',
                    'enum': ['media.convert', 'media.normalize', 'clean.analyze', 'narration'],
                    'description': 'What to do with each file dropped in the folder.',
                },
                'params': {
                    'type': 'object',
                    'description': 'Params of that kind, as studio_capabilities describes them.',
                },
                'keep_awake': {'type': 'boolean', 'description': 'Keep the server running while the folder is active.'},
            },
            ('path', 'kind'),
        ),
        _object(
            {
                'id': {
                    'type': 'integer',
                    'description': 'Id of the folder; use it to unregister it in the app or CLI.',
                },
                'path': _text('Absolute path of the folder.'),
                'kind': _text('Job kind applied to each file.'),
                'keep_awake': {'type': 'boolean'},
                'paused': {'type': 'boolean'},
            },
        ),
    ),
)
TOOL_NAMES = tuple(tool.name for tool in TOOLS)

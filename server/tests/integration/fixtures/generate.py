"""Caracterización: vuelca parsers.json y bloques.json, que fijan el comportamiento antes del refactor a src/.

Uso: uv run python server/tests/integration/fixtures/generate.py [CARPETA]   (por defecto, junto a este archivo)

Las fixtures se generaron con el código viejo de dev 31f9c20 y tests/test_caracterizacion.py compara contra ellas
con estas mismas funciones. La fuente es `actual()`: los 4 parsers por clave de comando y un objeto con
segmentos, etiquetas, preparar_bloques(modelo, segs, ref) y PARAMS_MOTOR (nuevo_tts() lo arma sobre src/).
Regenerar solo cuando un cambio de comportamiento es a propósito, y en un commit aparte.

Solo stdlib (grabar importa rich y questionary arriba). soundfile se reemplaza por un falso (toda referencia
dura 12 s: avisa en chatterbox y omnivoice) y la carpeta de referencias es sintética, así el resultado no depende
de audio gitignoreado ni de la GPU.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import os
import sys
import tempfile
import types
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]  # server/tests/integration/fixtures → raíz del repo
MODELS = ['voxcpm2', 'cosyvoice3', 'qwen-1.7b', 'qwen-0.6b', 'chatterbox', 'omnivoice', 'indextts']
# Las choices de --voice salen de server/data/narration/voices/<voz>/aprobacion.json, que está
# gitignoreado: se fijan las 9 voces
# aprobadas en el equipo donde se generó la base, para que el resultado sea el mismo en CI.
APPROVED_VOICES = [
    'karen-savage',
    'mpinedag',
    'yesid',
    'andrea',
    'hannah',
    'colombia-m',
    'peru-f',
    'venezuela-f',
    'vctk-p345',
]


# El módulo con construir_parser de cada comando (la clave 'script' de la fixture).
MODULES = {
    'narration tts': 'content_studio.narration.parser',
    'narration grabar': 'content_studio.narration.grabar.main',
    'narration voces': 'content_studio.narration.voices.main',
    'music': 'content_studio.music.parser',
}


def new_tts() -> types.SimpleNamespace:
    """La forma del tts viejo (preparar_bloques por nombre de modelo y PARAMS_MOTOR) sobre los módulos de src/."""
    from content_studio.narration.blocks import prepare_blocks
    from content_studio.narration.engines.registry import ENGINES
    from content_studio.narration.text.segments import segments, tags

    return types.SimpleNamespace(
        segments=segments,
        tags=tags,
        prepare_blocks=lambda m, secs, ref: prepare_blocks(ENGINES[m].create(), secs, ref),
        ENGINE_PARAMS={n: e.create().params for n, e in ENGINES.items()},
    )


def current() -> tuple[dict[str, tuple[str, types.ModuleType]], types.SimpleNamespace]:
    """Fuente actual: (clave → (nombre del módulo, módulo con construir_parser)) y lo que prepara los bloques."""
    return {c: (m, importlib.import_module(m)) for c, m in MODULES.items()}, new_tts()


def relative(v):
    """Rutas relativas a la raíz del repo y en formato posix, para que no dependan del checkout."""
    if isinstance(v, Path):
        try:
            return v.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            return v.as_posix()
    return v


def action(a: argparse.Action) -> dict:
    return {
        'option_strings': a.option_strings,
        'dest': a.dest,
        'action': type(a).__name__,
        'choices': list(a.choices) if a.choices is not None else None,
        'default': relative(a.default) if a.default is not argparse.SUPPRESS else '==SUPPRESS==',
        'required': a.required,
        'nargs': a.nargs,
        'const': a.const,
        'type': getattr(a.type, '__name__', None),
        'help': a.help,
        'metavar': a.metavar,
    }


def parsers(commands: dict[str, tuple[str, types.ModuleType]]) -> dict:
    out = {}
    # format_help depende del ancho de la terminal y de sys.argv[0], que pone el `usage: generar.py`
    with mock.patch.dict(os.environ, COLUMNS='120'), mock.patch.object(sys, 'argv', ['generar.py']):
        for key, (script, mod) in commands.items():
            with contextlib.ExitStack() as stack:
                if hasattr(mod, 'approved_voices'):
                    stack.enter_context(
                        mock.patch.object(mod, 'approved_voices', lambda _e: dict.fromkeys(APPROVED_VOICES, {}))
                    )
                ap = mod.build_parser()
            out[key] = {
                'script': script,
                'docstring': mod.__doc__,
                'description': ap.description,
                'acciones': [action(a) for a in ap._actions],
                'excluyentes': [
                    {'required': g.required, 'dests': [a.dest for a in g._group_actions]}
                    for g in ap._mutually_exclusive_groups
                ],
                'help': ap.format_help(),
            }
    return out


def synthetic_refs(d: Path) -> Path:
    """Referencias falsas: los estilos del guion, una sin transcripción y un clip de emoción para IndexTTS."""
    for e in ['expert', 'dramatic', 'energetic', 'soft', 'intimate']:
        (d / f'{e}.wav').write_bytes(b'')
        (d / f'{e}.txt').write_text(f'Transcripción de {e}.', encoding='utf-8')
    (d / 'emotions').mkdir()
    (d / 'emotions' / 'fear.wav').write_bytes(b'')
    return d


def blocks(tts) -> dict:
    false = types.SimpleNamespace(info=lambda _path: types.SimpleNamespace(duration=12.0))
    text = (HERE / 'regresion.txt').read_text(encoding='utf-8')
    with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(sys.modules, soundfile=false):
        ref = synthetic_refs(Path(tmp))

        def clean(v):
            if isinstance(v, Path):
                return v.relative_to(ref).as_posix()
            if isinstance(v, dict):
                return {k: clean(x) for k, x in v.items()}
            if isinstance(v, (list, tuple)):
                return [clean(x) for x in v]
            return v

        secs = tts.segments(text, 'expert')
        out = {
            'text': text,
            'style': 'expert',
            'segments': clean(secs),
            'tags': tts.tags(text),
            'models': {},
        }
        for m in MODELS:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                pb = tts.prepare_blocks(m, secs, ref)
            out['models'][m] = {
                'blocks': clean(pb),
                'stdout': output.getvalue(),
                'engine_params': tts.ENGINE_PARAMS.get(m, {}),
            }
    return out


def dump(folder: Path, name: str, data: dict) -> None:
    (folder / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
    folder.mkdir(parents=True, exist_ok=True)
    commands, tts = current()
    dump(folder, 'parsers.json', parsers(commands))
    dump(folder, 'bloques.json', blocks(tts))
    print(f'OK: {folder / "parsers.json"} y {folder / "bloques.json"}')

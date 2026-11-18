"""Caracterización: vuelca parsers.json y bloques.json, que fijan el comportamiento antes del refactor a src/.

Uso: uv run python tests/fixtures/generar.py [CARPETA]   (por defecto, junto a este archivo)

Las fixtures se generaron con el código viejo de dev 31f9c20 y tests/test_caracterizacion.py compara contra ellas
con estas mismas funciones. Para apuntar al código nuevo basta con otra fuente igual a `viejo()`: los 4 parsers
por clave de comando y un objeto con segmentos, etiquetas, preparar_bloques(modelo, segs, ref) y PARAMS_MOTOR.
Regenerar solo cuando un cambio de comportamiento es a propósito, y en un commit aparte.

Solo stdlib (grabar.py importa rich y questionary arriba). soundfile se reemplaza por un falso (toda referencia
dura 12 s: avisa en chatterbox y omnivoice) y la carpeta de referencias es sintética, así el resultado no depende
de audio gitignoreado ni de la GPU.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import types
from pathlib import Path
from unittest import mock

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
MODELOS = ['voxcpm2', 'cosyvoice3', 'qwen-1.7b', 'qwen-0.6b', 'chatterbox', 'omnivoice', 'indextts']
SCRIPTS = {'narration tts': 'narration/tts.py', 'narration grabar': 'narration/grabar.py',
           'narration voces': 'narration/voces.py', 'music': 'music/musica.py'}
# Las choices de --voz salen de narration/voces/<voz>/aprobacion.json, que está gitignoreado: se fijan las 9 voces
# aprobadas en el equipo donde se generó la base, para que el resultado sea el mismo en CI.
APROBADAS = ['karen-savage', 'mpinedag', 'yesid', 'andrea', 'hannah', 'colombia-m', 'peru-f', 'venezuela-f',
             'vctk-p345']


def cargar_script(script: str) -> types.ModuleType:
    """Carga un script viejo por su ruta, con su carpeta en sys.path (usan imports implícitos entre ellos)."""
    ruta = RAIZ / script
    if str(ruta.parent) not in sys.path:
        sys.path.insert(0, str(ruta.parent))
    spec = importlib.util.spec_from_file_location(f'_base_{ruta.stem}', ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Lo ya migrado a src/: el parser se importa por módulo (la clave 'script' de la fixture sigue siendo la del shim).
MODULOS = {'music': 'content_studio.music.parser'}


def viejo() -> tuple[dict[str, tuple[str, types.ModuleType]], types.ModuleType]:
    """Fuente actual: (clave → (script, módulo con construir_parser)) y el módulo que prepara los bloques."""
    mods = {c: importlib.import_module(MODULOS[c]) if c in MODULOS else cargar_script(s) for c, s in SCRIPTS.items()}
    return {c: (SCRIPTS[c], m) for c, m in mods.items()}, cargar_script('narration/tts.py')


def relativo(v):
    """Rutas relativas a la raíz del repo y en formato posix, para que no dependan del checkout."""
    if isinstance(v, Path):
        try:
            return v.resolve().relative_to(RAIZ).as_posix()
        except ValueError:
            return v.as_posix()
    return v


def accion(a: argparse.Action) -> dict:
    return {
        'option_strings': a.option_strings, 'dest': a.dest, 'accion': type(a).__name__,
        'choices': list(a.choices) if a.choices is not None else None,
        'default': relativo(a.default) if a.default is not argparse.SUPPRESS else '==SUPPRESS==',
        'required': a.required, 'nargs': a.nargs, 'const': a.const,
        'type': getattr(a.type, '__name__', None), 'help': a.help, 'metavar': a.metavar,
    }


def parsers(comandos: dict[str, tuple[str, types.ModuleType]]) -> dict:
    out = {}
    # format_help depende del ancho de la terminal y de sys.argv[0], que pone el `usage: generar.py`
    with mock.patch.dict(os.environ, COLUMNS='120'), mock.patch.object(sys, 'argv', ['generar.py']):
        for clave, (script, mod) in comandos.items():
            with contextlib.ExitStack() as pila:
                if hasattr(mod, 'aprobadas'):
                    pila.enter_context(mock.patch.object(mod, 'aprobadas', lambda _e: dict.fromkeys(APROBADAS, {})))
                ap = mod.construir_parser()
            out[clave] = {
                'script': script, 'docstring': mod.__doc__, 'description': ap.description,
                'acciones': [accion(a) for a in ap._actions],
                'excluyentes': [{'required': g.required, 'dests': [a.dest for a in g._group_actions]}
                                for g in ap._mutually_exclusive_groups],
                'help': ap.format_help(),
            }
    return out


def ref_sintetica(d: Path) -> Path:
    """Referencias falsas: los estilos del guion, una sin transcripción y un clip de emoción para IndexTTS."""
    for e in ['experta', 'dramatica', 'energica', 'suave', 'intima']:
        (d / f'{e}.wav').write_bytes(b'')
        (d / f'{e}.txt').write_text(f'Transcripción de {e}.', encoding='utf-8')
    (d / 'emociones').mkdir()
    (d / 'emociones' / 'miedo.wav').write_bytes(b'')
    return d


def bloques(tts) -> dict:
    falso = types.SimpleNamespace(info=lambda _ruta: types.SimpleNamespace(duration=12.0))
    texto = (AQUI / 'regresion.txt').read_text(encoding='utf-8')
    with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(sys.modules, soundfile=falso):
        ref = ref_sintetica(Path(tmp))

        def limpio(v):
            if isinstance(v, Path):
                return v.relative_to(ref).as_posix()
            if isinstance(v, dict):
                return {k: limpio(x) for k, x in v.items()}
            if isinstance(v, (list, tuple)):
                return [limpio(x) for x in v]
            return v

        segs = tts.segmentos(texto, 'experta')
        out = {'texto': texto, 'estilo': 'experta', 'segmentos': limpio(segs), 'etiquetas': tts.etiquetas(texto),
               'modelos': {}}
        for m in MODELOS:
            salida = io.StringIO()
            with contextlib.redirect_stdout(salida):
                pb = tts.preparar_bloques(m, segs, ref)
            out['modelos'][m] = {'bloques': limpio(pb), 'stdout': salida.getvalue(),
                                 'parametros_motor': tts.PARAMS_MOTOR.get(m, {})}
    return out


def volcar(carpeta: Path, nombre: str, datos: dict) -> None:
    (carpeta / nombre).write_text(json.dumps(datos, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    carpeta = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI
    comandos, tts = viejo()
    volcar(carpeta, 'parsers.json', parsers(comandos))
    volcar(carpeta, 'bloques.json', bloques(tts))
    print(f'OK: {carpeta / "parsers.json"} y {carpeta / "bloques.json"}')

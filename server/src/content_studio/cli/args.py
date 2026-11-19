"""Leer, completar y validar flags con el parser real de cada script. Solo stdlib (usa API privada de argparse)."""

from __future__ import annotations

import argparse
import re
from types import ModuleType

from content_studio.common.process import join


class ErrorArgs(Exception):
    """Error de los argumentos: flag inválido o valor que falta."""

    pass


def _error(msg: str):
    raise ErrorArgs(msg)


def flags(ap: argparse.ArgumentParser) -> list[argparse.Action]:
    """Acciones del parser que son flags (con `--`), sin la ayuda."""
    return [a for a in ap._actions if a.option_strings and not isinstance(a, argparse._HelpAction)]


def empty(v: object) -> bool:
    """Sin valor: None, False o lista vacía. Con `in (None, False, [])` se perdía el 0, porque 0 == False.

    >>> [empty(v) for v in (None, False, [], 0, 0.0, '')]
    [True, True, True, False, False, False]
    """
    return v is None or v is False or (isinstance(v, list) and not v)


def required(acc: argparse.Action, ap: argparse.ArgumentParser) -> bool:
    """True si el flag es obligatorio, directa o por un grupo mutuamente excluyente."""
    return acc.required or any(g.required and acc in g._group_actions for g in ap._mutually_exclusive_groups)


def es_booleano(acc: argparse.Action) -> bool:
    """True si el flag es un interruptor (store_true)."""
    return isinstance(acc, argparse._StoreTrueAction)


def _index(args: list[str], flag: str | None) -> int | None:
    """Posición del token de `flag`, que puede venir como --flag=valor o abreviado (--mod)."""
    for k, t in enumerate(args):
        c = t.split('=', 1)[0]
        if flag and t.startswith('-') and (c == flag or (len(c) > 2 and flag.startswith(c))):
            return k
    return None


def leer(ap: argparse.ArgumentParser, args: list[str]) -> tuple[dict, list[str]]:
    """Flags válidos que vinieron en `args` (dest -> valor), sin exigir los obligatorios. Un flag inválido
    se descarta con su valor (y se avisa) para conservar el resto."""
    ap.error = _error
    for acc in flags(ap):
        acc.required = False
    for g in ap._mutually_exclusive_groups:
        g.required = False
    notices = []
    while True:
        try:
            ns, extra = ap.parse_known_args(args)
            break
        except ErrorArgs as e:
            m = re.search(r'argument (-[-\w]+)', str(e))  # el error de argparse cita el flag completo
            i = _index(args, m and m[1])
            if i is None:
                return {}, [str(e)]
            j = i + 1
            while '=' not in args[i] and j < len(args) and not args[j].startswith('--'):
                j += 1
            notices.append(f'{join(args[i:j])} no es válido; lo eliges abajo')
            args = args[:i] + args[j:]
    if extra:
        notices.append(f'no reconocido: {join(extra)}')
    dados = {
        acc.dest: getattr(ns, acc.dest)
        for acc in flags(ap)
        if any(
            (c := t.split('=', 1)[0]) == o or (len(c) > 2 and c[0] == '-' and o.startswith(c))  # o abreviado
            for t in args
            for o in acc.option_strings
        )
    }
    return dados, notices


def a_argv(ap: argparse.ArgumentParser, values: dict) -> list[str]:
    """Convierte los valores del asistente de nuevo en una lista de argumentos."""
    argv = []
    for acc in flags(ap):
        if acc.dest not in values or empty(values[acc.dest]):
            continue
        v = values[acc.dest]
        if es_booleano(acc):
            argv.append(acc.option_strings[0])
        elif isinstance(v, list):
            argv += [acc.option_strings[0], *map(str, v)]
        else:
            argv += [acc.option_strings[0], str(v)]
    return argv


def validate(mod: ModuleType, argv: list[str]) -> str | None:
    """Error del parser real del script con estos flags, o None."""
    ap = mod.build_parser()
    ap.error = _error
    try:
        ap.parse_args(argv)
    except ErrorArgs as e:
        return str(e)
    return None

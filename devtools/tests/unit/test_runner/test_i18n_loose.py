"""Textos sueltos en Python y TS (spec 007, AC-4, AC-5 y D-8): la misma regla de «qué cuenta como texto» en los dos."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from devtools.test_runner.i18n_loose import check_loose_python, check_loose_ts, is_prose

FIXTURES = Path(__file__).resolve().parents[2] / 'fixtures' / 'i18n'
CASES = json.loads((FIXTURES / 'prose-cases.json').read_text(encoding='utf-8'))


def write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding='utf-8')
    return path


@pytest.mark.parametrize('case', CASES, ids=[case['text'] or 'vacio' for case in CASES])
def test_the_prose_rule_in_python_matches_the_table(case):
    assert is_prose(case['text']) == case['prose']


def test_the_prose_rule_in_typescript_matches_the_same_table(tmp_path):
    path = write(
        tmp_path,
        'table.ts',
        '\n'.join(f'const c{index} = {json.dumps(case["text"])};' for index, case in enumerate(CASES)) + '\n',
    )

    flagged = [finding.line for finding in check_loose_ts([path])]

    expected = [index + 1 for index, case in enumerate(CASES) if case['prose']]
    assert flagged == expected


def test_ac4_flags_visible_text_in_an_http_exception_and_in_a_response(tmp_path):
    path = write(
        tmp_path,
        'routes.py',
        "from fastapi import HTTPException\n\n\ndef f():\n    raise HTTPException(400, detail='Falta el texto')\n\n\n"
        "def g():\n    return {'message': 'Listo'}\n",
    )

    findings = check_loose_python([path])

    assert [(finding.line, finding.text) for finding in findings] == [(5, 'Falta el texto'), (9, 'Listo')]


def test_ac4_leaves_docstrings_logs_codes_keys_and_internal_messages_alone(tmp_path):
    path = write(
        tmp_path,
        'service.py',
        '"""Módulo de prueba: documentación en español."""\n'
        'import logging\n\n'
        'from content_studio.api.errors import ApiError\n\n'
        'log = logging.getLogger(__name__)\n\n\n'
        'def f(job_id):\n'
        '    """Busca el trabajo y, si no existe, avisa."""\n'
        "    log.info('job started')\n"
        '    if job_id is None:\n'
        "        raise ApiError(404, 'not_found')\n"
        '    if job_id < 0:\n'
        "        raise ValueError('bad seed')\n"
        "    return {'code': 'job_not_found', 'status': 'ok'}\n",
    )

    assert check_loose_python([path]) == []


def test_ac4_an_ignore_marker_without_a_reason_is_an_error(tmp_path):
    path = write(tmp_path, 'routes.py', "def f():\n    return {'message': 'Listo'}  # i18n-ignore:\n")

    findings = check_loose_python([path])

    assert len(findings) == 1
    assert 'reason' in findings[0].message()


def test_ac4_an_ignore_marker_with_a_reason_silences_the_line(tmp_path):
    path = write(tmp_path, 'routes.py', "def f():\n    return {'message': 'Listo'}  # i18n-ignore: texto técnico\n")

    assert check_loose_python([path]) == []


def test_ac5_flags_visible_text_in_tsx_with_file_line_and_text():
    findings = check_loose_ts([FIXTURES / 'client' / 'flagged.tsx'])

    assert [(finding.line, finding.text) for finding in findings] == [
        (2, 'Abrir carpeta'),
        (3, 'Listo'),
        (6, 'Cerrar'),
        (7, 'Hola ${name}'),
    ]
    assert findings[0].message() == (
        f'{findings[0].path}:2: loose text "Abrir carpeta". Move it to messages/*.json and use t(\'…\'), '
        'or mark the line with // i18n-ignore: <reason>.'
    )


def test_ac5_leaves_classes_imports_types_keys_and_t_calls_alone():
    assert check_loose_ts([FIXTURES / 'client' / 'allowed.tsx']) == []


def test_ac5_class_strings_in_variant_maps_are_not_text(tmp_path):
    """Las clases de Tailwind de un `cva` o un objeto de variantes no son texto (spec 008, primitivas de shadcn)."""
    path = write(
        tmp_path,
        'Badge.tsx',
        "const variants = cva('inline-flex gap-1', {\n"
        "  variants: { variant: { default: 'bg-primary text-primary-foreground hover:bg-primary/80' } },\n"
        '});\n'
        "export const label = 'Cerrar sesión';\n"
        "export const more = 'hover:underline text-sm';\n",
    )

    findings = check_loose_ts([path])

    assert [(finding.line, finding.text) for finding in findings] == [(4, 'Cerrar sesión')]


def test_ac5_an_ignore_marker_in_tsx_needs_a_reason(tmp_path):
    path = write(tmp_path, 'Foo.tsx', "export const x = 'Hola mundo'; // i18n-ignore:\n")

    findings = check_loose_ts([path])

    assert len(findings) == 1
    assert 'reason' in findings[0].message()

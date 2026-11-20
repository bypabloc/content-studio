"""Etapa i18n del test-runner: catálogos parejos (spec 007, AC-1 y D-8). Claves en uso y textos sueltos van aparte."""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from pathlib import Path

from devtools import paths
from devtools.test_runner.i18n import check_catalogs, check_usage, run
from devtools.test_runner.main import GROUPS
from devtools.test_runner.spelling import run as run_spelling

VALID = Path(__file__).resolve().parents[2] / 'fixtures' / 'i18n' / 'catalogs' / 'valid'


def copy_valid(tmp_path: Path) -> Path:
    target = tmp_path / 'messages'
    shutil.copytree(VALID, target)
    return target


def edit(catalog: Path, locale: str, change: Callable[[dict], dict]) -> None:
    path = catalog / f'{locale}.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    path.write_text(json.dumps(change(data), ensure_ascii=False), encoding='utf-8')


def test_ac1_valid_catalogs_have_no_problems():
    assert check_catalogs(VALID) == []


def test_ac1_a_key_missing_in_a_locale_is_reported_with_file_and_key(tmp_path):
    catalog = copy_valid(tmp_path)
    edit(catalog, 'en', lambda data: {key: text for key, text in data.items() if key != 'b.farewell'})

    problems = check_catalogs(catalog)

    assert len(problems) == 1
    assert 'en.json' in problems[0] and 'b.farewell' in problems[0]


def test_ac1_a_locale_with_other_parameters_is_reported(tmp_path):
    catalog = copy_valid(tmp_path)
    edit(catalog, 'en', lambda data: {**data, 'a.greeting': 'Hi'})

    problems = check_catalogs(catalog)

    assert len(problems) == 1
    assert 'en.json' in problems[0] and 'a.greeting' in problems[0]


def test_ac1_keys_out_of_alphabetical_order_are_reported(tmp_path):
    catalog = copy_valid(tmp_path)
    edit(catalog, 'es', lambda data: dict(reversed(list(data.items()))))

    problems = check_catalogs(catalog)

    assert len(problems) == 1
    assert 'es.json' in problems[0] and 'alphabetical' in problems[0]


def test_ac1_a_repeated_key_is_reported(tmp_path):
    catalog = copy_valid(tmp_path)
    (catalog / 'es.json').write_text(
        '{"a.greeting": "Hola", "a.greeting": "Hola {name}", "b.farewell": "Adiós"}', encoding='utf-8'
    )

    problems = check_catalogs(catalog)

    assert len(problems) == 1
    assert 'a.greeting' in problems[0] and 'twice' in problems[0]


def test_ac1_an_empty_value_is_reported(tmp_path):
    catalog = copy_valid(tmp_path)
    edit(catalog, 'en', lambda data: {**data, 'b.farewell': '  '})

    problems = check_catalogs(catalog)

    assert len(problems) == 1
    assert 'en.json' in problems[0] and 'b.farewell' in problems[0]


def test_ac1_a_file_that_is_not_json_is_reported(tmp_path):
    catalog = copy_valid(tmp_path)
    (catalog / 'pt.json').write_text('{"a.greeting": ', encoding='utf-8')

    problems = check_catalogs(catalog)

    assert len(problems) == 1
    assert 'pt.json' in problems[0] and 'JSON' in problems[0]


def test_ac1_the_real_catalogs_have_no_problems():
    assert check_catalogs() == []


def test_ac1_run_reports_the_stage_with_the_problems(tmp_path):
    catalog = copy_valid(tmp_path)
    edit(catalog, 'en', lambda data: {key: text for key, text in data.items() if key != 'b.farewell'})

    result = run([], catalog_dir=catalog)

    assert result['stage'] == 'i18n'
    assert result['status'] == 'fail'
    assert 'b.farewell' in result['detail']


def test_ac1_run_passes_on_the_real_catalogs():
    assert run([]) == {'stage': 'i18n', 'status': 'pass', 'detail': ''}


def make_repo(tmp_path: Path, files: dict[str, str]) -> Path:
    root = tmp_path / 'repo'
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    return root


def usage(tmp_path: Path, files: dict[str, str], catalog: dict[str, str], prefixes=()) -> list[str]:
    root = make_repo(tmp_path, files)
    return check_usage(root, catalog, {'dynamicPrefixes': list(prefixes)})


def test_ac3_a_client_key_without_text_is_reported(tmp_path):
    problems = usage(
        tmp_path,
        {'client/src/app/Foo.tsx': "export const label = t('missing.key');\n"},
        {'nav.settings': 'Ajustes'},
    )

    assert any('missing.key' in problem and 'Foo.tsx' in problem for problem in problems)


def test_ac3_a_key_nobody_uses_is_reported_as_orphan(tmp_path):
    problems = usage(
        tmp_path,
        {'client/src/app/Foo.tsx': "export const label = t('nav.settings');\n"},
        {'nav.settings': 'Ajustes', 'orphan.key': 'Huérfana'},
    )

    assert problems == ['messages/es.json: key "orphan.key" is not used']


def test_ac3_a_key_under_a_declared_dynamic_prefix_is_not_an_orphan(tmp_path):
    problems = usage(tmp_path, {}, {'queue.status.error': 'Error'}, prefixes=['queue.status.'])

    assert problems == []


def test_ac3_an_api_code_without_its_text_is_reported(tmp_path):
    problems = usage(
        tmp_path,
        {'server/src/content_studio/api/routes/x.py': "def f():\n    raise ApiError(404, 'sin_texto')\n"},
        {},
    )

    assert any('sin_texto' in problem and 'x.py' in problem for problem in problems)


def test_ac3_an_api_code_with_its_text_passes(tmp_path):
    problems = usage(
        tmp_path,
        {'server/src/content_studio/api/routes/x.py': "def f():\n    raise ApiError(404, 'job_not_found')\n"},
        {'error.job_not_found': 'No existe el trabajo.'},
    )

    assert problems == []


def test_ac3_a_code_in_a_validation_result_needs_its_text_too(tmp_path):
    problems = usage(
        tmp_path,
        {'server/src/content_studio/services/x.py': "def validate(p):\n    return {'code': 'otro', 'params': {}}\n"},
        {},
    )

    assert any('otro' in problem for problem in problems)


def test_ac3_a_dynamic_prefix_without_keys_is_reported(tmp_path):
    problems = usage(tmp_path, {}, {}, prefixes=['queue.kind.'])

    assert any('queue.kind.' in problem for problem in problems)


def test_ac3_a_t_call_in_python_is_a_usage_of_its_key(tmp_path):
    """El server también usa claves con `t('…')` (messages.t): cuentan como uso, igual que las del client."""
    source = "from content_studio import messages\nTEXT = messages.t('only.python')\n"
    problems = usage(
        tmp_path,
        {'server/src/content_studio/narration/x.py': source},
        {'only.python': 'Solo en Python'},
    )

    assert problems == []


def test_ac3_a_python_t_call_without_its_text_is_reported(tmp_path):
    source = "from content_studio import messages\nTEXT = messages.t('sin.texto')\n"
    problems = usage(tmp_path, {'server/src/content_studio/narration/x.py': source}, {})

    assert any('sin.texto' in problem and 'x.py' in problem for problem in problems)


def test_ac3_the_real_repo_has_no_usage_problems():
    assert check_usage() == []


def test_ac6_the_all_group_and_the_pre_commit_run_the_i18n_stage():
    """`all` y el pre-commit corren la etapa i18n: un texto suelto no llega al commit (spec 007, AC-6)."""
    hook = (paths.ROOT / '.git-hooks' / 'pre-commit').read_text(encoding='utf-8')

    assert 'i18n' in GROUPS['all']
    assert 'i18n' in hook.split('--type=')[1].split(' ')[0].split(',')


def test_ac10_spelling_fails_on_a_misspelled_english_catalog(tmp_path):
    """La ortografía falla con una palabra mal escrita en un catálogo en inglés (spec 007, AC-10).

    El archivo se crea en tmp_path: si fuera versionado, el changeset de la etapa lo leería y fallaría el gate.
    """
    misspelled = tmp_path / 'en.json'
    misspelled.write_text('{"a.greeting": "Helllo wrld"}', encoding='utf-8')

    result = run_spelling([misspelled])

    assert result['status'] == 'fail'
    assert 'Helllo' in result['detail']


def test_ac10_spelling_passes_on_the_real_catalogs():
    catalogs = [
        paths.ROOT / 'server' / 'src' / 'content_studio' / 'messages' / f'{locale}.json'
        for locale in ('es', 'en', 'pt')
    ]

    assert run_spelling(catalogs)['status'] == 'pass'

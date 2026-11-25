"""Recetas reproducibles y validadas, spec 012 AC-2."""

import re
from pathlib import Path

import pytest

from content_studio.engines import recipes


def test_ac2_loads_a_pinned_recipe_for_every_existing_engine():
    """Una receta por motor con revisiones completas de Git y Hugging Face."""
    expected = {
        'voxcpm2',
        'cosyvoice3',
        'qwen-1.7b',
        'qwen-0.6b',
        'chatterbox',
        'omnivoice',
        'indextts',
        'acestep',
        'heartmula',
    }
    assert expected <= {recipe.engine for recipe in recipes.load_all()}
    for name in expected:
        recipe = recipes.load(name)
        assert recipe.engine == name
        assert recipe.venv
        assert recipe.steps[0]['kind'] == 'python'
        assert recipe.steps[-1]['kind'] == 'verify'
        for step in recipe.steps:
            if step['kind'] == 'git':
                assert re.fullmatch(r'[0-9a-f]{40}', step['commit'])
            if step['kind'] == 'hf':
                assert re.fullmatch(r'[0-9a-f]{40}', step['revision'])
            if step['kind'] == 'pip':
                for package in step['packages']:
                    if re.match(r'^(torch|torchaudio|torchvision)(?:[=<>~! ]|$)', package):
                        assert '==' in package and '*' not in package


def _valid_recipe():
    """Receta mínima que deja un entorno y verifica su import."""
    return {
        'engine': 'fake',
        'family': 'narration',
        'size_gb': 4.8,
        'vram_gb': 5.5,
        'cpu': False,
        'license': 'MIT',
        'steps': [
            {'kind': 'python', 'version': '3.12'},
            {'kind': 'venv', 'path': '.venv-fake'},
            {'kind': 'pip', 'packages': ['torch==2.11.0']},
            {'kind': 'verify', 'import': 'fake'},
        ],
    }


def test_ac2_rejects_an_unknown_step_and_names_it():
    """Una receta incorrecta indica qué paso falló."""
    data = _valid_recipe()
    data['steps'][2] = {'kind': 'unknown'}
    with pytest.raises(ValueError, match='unknown'):
        recipes.validate(data)


@pytest.mark.parametrize(
    ('index', 'step', 'message'),
    [
        (1, {'kind': 'venv', 'path': '../outside'}, 'path'),
        (2, {'kind': 'pip', 'packages': ['torch>=2.0']}, 'torch'),
        (2, {'kind': 'hf', 'repo': 'owner/model', 'revision': 'main', 'into': 'hf'}, 'revision'),
        (2, {'kind': 'git', 'url': 'https://github.com/owner/repo', 'into': 'repo'}, 'commit'),
    ],
)
def test_ac2_validates_revisions_dependencies_and_local_paths(index, step, message):
    """Cada paso valida sus campos antes de que el instalador lo ejecute."""
    data = _valid_recipe()
    data['steps'][index] = step
    with pytest.raises(ValueError, match=message):
        recipes.validate(data)


def test_ac5_the_vision_recipe_pins_opencv_and_only_the_yunet_model():
    """AC-5: la receta de visión fija OpenCV y baja solo el .onnx de 2023mar, en CPU."""
    recipe = recipes.load('vision')

    assert (recipe.family, recipe.cpu, recipe.venv) == ('vision', True, '.venv-vision')
    pip = next(step for step in recipe.steps if step['kind'] == 'pip')
    assert pip['packages'] == ['opencv-python==5.1.0.95', 'huggingface-hub==2.4.0']
    hf = next(step for step in recipe.steps if step['kind'] == 'hf')
    assert hf['allow_patterns'] == ['face_detection_yunet_2023mar.onnx']


def test_every_recipe_that_downloads_from_hugging_face_pins_huggingface_hub():
    """El paso `hf` importa `huggingface_hub` dentro del venv del motor: la receta debe fijarlo o el paso falla."""
    for recipe in recipes.load_all():
        if any(step['kind'] == 'hf' for step in recipe.steps):
            packages = [package for step in recipe.steps if step['kind'] == 'pip' for package in step['packages']]
            assert any(re.fullmatch(r'huggingface-hub==[\w.]+', package) for package in packages), recipe.engine


def test_ac1_llama_cpp_recipe_downloads_pinned_release_zips():
    """Spec 021 AC-1: el runtime baja dos zips del release fijado, con sha256, y verifica llama-server."""
    recipe = recipes.load('llama-cpp')
    downloads = [step for step in recipe.steps if step['kind'] == 'download']
    assert recipe.family == 'assistant'
    assert len(downloads) == 2
    for step in downloads:
        assert step['url'].startswith('https://github.com/ggml-org/llama.cpp/releases/download/')
        assert re.fullmatch(r'[0-9a-f]{64}', step['sha256'])
        assert step['extract'] == 'bin'
    assert recipe.steps[-1]['run'] == ['bin/llama-server.exe', '--version']


def _download(**changes):
    step = {'kind': 'download', 'url': 'https://example.com/a.zip', 'sha256': '0' * 64, 'extract': 'bin'}
    return {**step, **changes}


@pytest.mark.parametrize(
    ('step', 'message'),
    [
        (_download(sha256='abc'), 'sha256'),
        (_download(url='http://example.com/a.zip'), 'url'),
        (_download(extract='../out'), 'extract'),
        ({'kind': 'verify', 'import': 'json', 'run': ['../llama-server.exe']}, 'run'),
    ],
)
def test_ac1_rejects_an_invalid_download_or_run(step, message):
    """Una descarga sin sha256 completo, sin https o fuera de la carpeta del motor no se acepta."""
    data = _valid_recipe()
    data['steps'][2] = step
    if step['kind'] == 'verify':
        data['steps'][3] = step
        del data['steps'][2]
    with pytest.raises(ValueError, match=message):
        recipes.validate(data)


def test_ac1_every_engine_below_pinned_python_has_warning():
    """AC-1 (spec 026): toda receta por debajo de .python-version tiene su ficha 026-<motor>-version."""
    root = Path(__file__).resolve().parents[6]
    pinned = tuple(int(part) for part in (root / '.python-version').read_text(encoding='utf-8').strip().split('.')[:2])
    missing = []
    for recipe in recipes.load_all():
        python = next(step['version'] for step in recipe.steps if step['kind'] == 'python')
        version = tuple(int(part) for part in python.split('.')[:2])
        warning_file = root / 'docs/process/WARNING' / f'026-{recipe.engine}-version.md'
        if version < pinned and not warning_file.is_file():
            missing.append(recipe.engine)
    assert missing == [], f'sin ficha 026-<motor>-version: {missing}'


def test_ac1_pyannote_recipe():
    """AC-1 (spec 034): la receta de pyannote es de diarización, fija versiones y pide el repositorio restringido."""
    recipe = recipes.load('pyannote')

    assert (recipe.family, recipe.venv) == ('diarization', '.venv-diarize')
    assert recipe.steps[0] == {'kind': 'python', 'version': '3.14'}
    packages = [package for step in recipe.steps if step['kind'] == 'pip' for package in step['packages']]
    for name in ('torch', 'torchaudio', 'pyannote.audio', 'torchcodec', 'huggingface-hub'):
        assert any(package.split('==')[0] == name and '==' in package for package in packages), name
    hf = next(step for step in recipe.steps if step['kind'] == 'hf')
    assert hf['repo'] == 'pyannote/speaker-diarization-community-1'
    assert re.fullmatch(r'[0-9a-f]{40}', hf['revision'])
    assert hf['gated'] is True
    assert hf['into'] == 'models/community-1'
    assert recipe.gated is True
    assert recipe.steps[-1] == {'kind': 'verify', 'import': 'pyannote.audio'}


def test_ac1_gated_is_a_boolean_on_hf_steps():
    """AC-1 (spec 034): un paso hf declara gated como booleano; cualquier otro valor se rechaza."""
    hf = {'kind': 'hf', 'repo': 'owner/model', 'revision': '0' * 40, 'into': 'hf'}
    data = _valid_recipe()
    data['steps'][2] = {**hf, 'gated': True}
    assert recipes.validate(data).gated is True
    data['steps'][2] = {**hf, 'gated': 'yes'}
    with pytest.raises(ValueError, match='gated'):
        recipes.validate(data)

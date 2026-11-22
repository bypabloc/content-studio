"""Recetas reproducibles y validadas, spec 012 AC-2."""

import re

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
    assert pip['packages'] == ['opencv-python==4.13.0.92', 'huggingface-hub==0.36.2']
    hf = next(step for step in recipe.steps if step['kind'] == 'hf')
    assert hf['allow_patterns'] == ['face_detection_yunet_2023mar.onnx']


def test_every_recipe_that_downloads_from_hugging_face_pins_huggingface_hub():
    """El paso `hf` importa `huggingface_hub` dentro del venv del motor: la receta debe fijarlo o el paso falla."""
    for recipe in recipes.load_all():
        if any(step['kind'] == 'hf' for step in recipe.steps):
            packages = [package for step in recipe.steps if step['kind'] == 'pip' for package in step['packages']]
            assert any(re.fullmatch(r'huggingface-hub==[\w.]+', package) for package in packages), recipe.engine

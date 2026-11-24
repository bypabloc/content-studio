"""Catálogo de modelos LLM, spec 021 AC-1."""

import re

from content_studio.engines import recipes
from content_studio.llm import models


def test_ac1_every_model_has_a_pinned_recipe_with_its_gguf():
    """Cada modelo se instala con su receta: repo y revisión fijados y solo su GGUF Q4_K_M."""
    assert models.RECOMMENDED in models.MODELS
    for name, spec in models.MODELS.items():
        recipe = recipes.load(name)
        assert recipe.family == 'assistant'
        hf = next(step for step in recipe.steps if step['kind'] == 'hf')
        assert hf['repo'] == spec.repo
        assert re.fullmatch(r'[0-9a-f]{40}', hf['revision'])
        assert hf['allow_patterns'] == [spec.file]
        assert spec.file.endswith('Q4_K_M.gguf')
        assert spec.context == 8192


def test_paths_follow_the_installer_layout(tmp_path):
    """El GGUF queda en <motores>/<modelo>/assistant/models y llama-server en llama-cpp/assistant/bin."""
    spec = models.MODELS['gemma-4-e4b']
    assert models.gguf_path('gemma-4-e4b', tmp_path) == tmp_path / 'gemma-4-e4b' / 'assistant' / 'models' / spec.file
    assert models.server_path(tmp_path).parent == tmp_path / 'llama-cpp' / 'assistant' / 'bin'


def test_status_reports_which_models_are_installed(tmp_path):
    """Un modelo cuenta como instalado cuando su GGUF existe; el ★ es el recomendado."""
    gguf = models.gguf_path('qwen3.5-9b', tmp_path)
    gguf.parent.mkdir(parents=True)
    gguf.write_bytes(b'gguf')

    status = {row['model']: row for row in models.status(tmp_path)}

    assert status['qwen3.5-9b']['installed'] is True
    assert status['gemma-4-e4b']['installed'] is False
    assert status[models.RECOMMENDED]['recommended'] is True


def test_every_model_turns_thinking_off():
    """D-4: Gemma 4 E4B pensaba ~700 tokens por pedido aunque el sistema no lleve <|think|>; los dos lo apagan."""
    for spec in models.MODELS.values():
        assert spec.extra == {'chat_template_kwargs': {'enable_thinking': False}}

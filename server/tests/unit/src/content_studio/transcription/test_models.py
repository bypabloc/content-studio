"""Catálogo de modelos de faster-whisper (spec 013, D-1 y AC-9) y su receta pineada."""

from __future__ import annotations

from content_studio.engines import recipes
from content_studio.transcription import models


def test_ac9_the_recommended_model_is_large_v3_turbo():
    """AC-9: large-v3-turbo es el recomendado (★) del selector."""
    assert models.RECOMMENDED == 'large-v3-turbo'
    assert models.recommended() == 'large-v3-turbo'


def test_the_catalog_has_the_four_models_with_repo_size_and_vram():
    """Cuatro modelos, cada uno con su repo de Hugging Face, su tamaño y su VRAM aproximada."""
    assert set(models.MODELS) == {'small', 'medium', 'large-v3-turbo', 'large-v3'}
    for name, spec in models.MODELS.items():
        assert spec.repo.count('/') == 1, name
        assert spec.size_gb > 0
        assert spec.vram_gb > 0


def test_each_model_maps_to_its_hub_repo():
    """El nombre del modelo se resuelve a su repo de Hugging Face."""
    assert models.repo('small') == 'Systran/faster-whisper-small'
    assert models.repo('large-v3') == 'Systran/faster-whisper-large-v3'


def test_the_faster_whisper_recipe_is_pinned_and_ends_with_verify():
    """La receta del motor fija versiones con ==, incluidas las bibliotecas CUDA de Windows, y termina en verify."""
    recipe = recipes.load('faster-whisper')

    assert recipe.venv == '.venv-whisper'
    assert recipe.steps[0]['kind'] == 'python'
    assert recipe.steps[-1] == {'kind': 'verify', 'import': 'faster_whisper'}
    packages = [p for step in recipe.steps if step['kind'] == 'pip' for p in step['packages']]
    assert any(p.startswith('faster-whisper==') for p in packages)
    assert any(p.startswith('nvidia-cublas-cu12==') for p in packages)
    assert all('==' in p for p in packages)


def test_downloaded_is_true_only_when_the_snapshot_has_its_model_file(tmp_path):
    """AC-9: un modelo está descargado si su snapshot de Hugging Face trae `model.bin`, no antes."""
    snapshot = tmp_path / 'models--Systran--faster-whisper-small' / 'snapshots' / 'abc123'
    snapshot.mkdir(parents=True)
    assert models.downloaded('small', tmp_path) is False

    (snapshot / 'model.bin').write_bytes(b'')

    assert models.downloaded('small', tmp_path) is True
    assert models.downloaded('medium', tmp_path) is False


def test_status_lists_every_model_with_size_recommendation_and_download_state(tmp_path):
    """El estado de los modelos: tamaño, VRAM, cuál es el recomendado y cuáles ya están en la caché."""
    entries = {entry['model']: entry for entry in models.status(tmp_path)}

    assert set(entries) == set(models.MODELS)
    assert entries['large-v3-turbo']['recommended'] is True
    assert entries['small']['recommended'] is False
    assert entries['small']['size_gb'] == models.MODELS['small'].size_gb
    assert all(entry['downloaded'] is False for entry in entries.values())

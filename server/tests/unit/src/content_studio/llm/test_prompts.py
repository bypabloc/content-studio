"""Plantillas de los prompts, spec 021 D-4."""

import pytest

from content_studio.llm import prompts


def test_render_replaces_every_marker(tmp_path, monkeypatch):
    """Cada {{variable}} se reemplaza; una variable que falta es un error, no un prompt a medias."""
    (tmp_path / 'demo.md').write_text('Hola {{name}}, tienes {{count}} avisos.', encoding='utf-8')
    monkeypatch.setattr(prompts, 'DIRECTORY', tmp_path)

    assert prompts.render('demo', name='Ana', count=3) == 'Hola Ana, tienes 3 avisos.'
    with pytest.raises(KeyError, match='count'):
        prompts.render('demo', name='Ana')


def test_every_shipped_prompt_has_its_markers_filled():
    """Los prompts de las tareas existen y solo usan las variables que les pasa su tarea."""
    for name in ('script_review', 'music_caption'):
        assert '{{' in (prompts.DIRECTORY / f'{name}.md').read_text(encoding='utf-8')


def test_guide_rules_come_from_the_script_guide():
    """Las reglas obligatorias se leen de formato-guion.md (no se copian): de la 1 a la 22."""
    rules = prompts.guide_rules()

    assert rules.startswith('1. ')
    assert '13. Números en letras' in rules
    assert '22. ' in rules
    assert '23. ' not in rules

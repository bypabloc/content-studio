"""devtools agent-context: tamaño de lo que cargan los agentes."""

from __future__ import annotations

from devtools import agent_context, paths


def test_context_agents_the_repo_without_failures():
    agents, failures = agent_context.measure(paths.ROOT)
    assert failures == []
    assert agents['antigravity']['files'] > 0


def test_agent_context_accepts_rules_with_crlf(tmp_path):
    """Regresión: en Windows, git hace checkout con CRLF y el frontmatter no se reconocía."""
    (tmp_path / '.agents/rules').mkdir(parents=True)
    (tmp_path / '.agents/rules/x.md').write_bytes(b'---\r\ntrigger: always_on\r\n---\r\n\r\n# X\r\n')
    assert agent_context.measure(tmp_path)[1] == []


def test_context_agents_detects_trigger_invalid(tmp_path):
    (tmp_path / '.agents/rules').mkdir(parents=True)
    (tmp_path / '.agents/rules/x.md').write_text('---\ntrigger: siempre\n---\n# X\n')
    assert any('trigger' in f for f in agent_context.measure(tmp_path)[1])

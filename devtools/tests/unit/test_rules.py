"""devtools rules: sincronía de reglas y skills entre .agents/ y .claude/."""

from __future__ import annotations

from devtools import rules


def test_rules_syncs_keeping_the_frontmatter_of_claude(tmp_path):
    (tmp_path / '.agents/rules').mkdir(parents=True)
    (tmp_path / '.claude/rules').mkdir(parents=True)
    (tmp_path / '.agents/rules/r.md').write_text('---\ntrigger: always_on\n---\n\n# R nueva\n', newline='\n')
    (tmp_path / '.claude/rules/r.md').write_text('---\npaths:\n  - "src/**"\n---\n\n# R vieja\n', newline='\n')
    (tmp_path / '.claude/rules/huerfana.md').write_text('# H\n')
    assert len(rules.differences(tmp_path)) == 2
    assert rules.sync(tmp_path) == ['.claude/rules/r.md']
    text = (tmp_path / '.claude/rules/r.md').read_text()
    assert text.startswith('---\npaths:') and text.endswith('# R nueva\n')
    assert rules.differences(tmp_path) == ['.claude/rules/huerfana.md has no source in .agents/rules/']

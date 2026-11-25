"""Spec 029, fase 1: el catálogo de herramientas (AC-1): nombres exactos, esquemas y ninguna administrativa."""

from content_studio.mcp_server import catalog

EXPECTED = (
    'studio_capabilities',
    'studio_narrate',
    'studio_make_music',
    'studio_transcribe',
    'studio_clean_silences',
    'studio_convert_media',
    'studio_submit_job',
    'studio_get_job',
    'studio_wait_job',
    'studio_cancel_job',
)
ADMIN_WORDS = ('engine', 'storage', 'setting', 'fs', 'trash', 'install', 'uninstall', 'delete', 'remove')


def test_ac1_ten_tools_with_schemas_and_no_admin():
    assert catalog.TOOL_NAMES == EXPECTED
    for tool in catalog.TOOLS:
        assert tool.input_schema['type'] == 'object'
        assert tool.output_schema['type'] == 'object'
        assert not any(word in tool.name for word in ADMIN_WORDS)


def test_read_only_and_destructive_annotations_match_02():
    assert {tool.name for tool in catalog.TOOLS if tool.read_only} == {
        'studio_capabilities',
        'studio_get_job',
        'studio_wait_job',
    }
    assert {tool.name for tool in catalog.TOOLS if tool.destructive} == {'studio_cancel_job'}

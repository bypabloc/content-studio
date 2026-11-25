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


def _type_lists(node):
    """Cada `type` que es una lista (un campo anulable): los clientes de un solo tipo no siempre la aceptan."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == 'type' and isinstance(value, list):
                yield value
            yield from _type_lists(value)
    elif isinstance(node, list):
        for item in node:
            yield from _type_lists(item)


def test_schemas_use_one_type_per_branch():
    for tool in catalog.TOOLS:
        assert list(_type_lists(tool.input_schema)) == []
        assert list(_type_lists(tool.output_schema)) == []

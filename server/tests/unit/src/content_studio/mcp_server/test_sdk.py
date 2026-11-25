"""Spec 029, fase 1: la traducción del catálogo y de los resultados al protocolo del SDK, sin servidor."""

from mcp import types

from content_studio.mcp_server import catalog, sdk
from content_studio.mcp_server.bridge import ToolResult


def test_annotations_come_from_the_catalog():
    by_name = {tool.name: tool for tool in catalog.TOOLS}
    get = sdk._tool(types, by_name['studio_get_job'])
    cancel = sdk._tool(types, by_name['studio_cancel_job'])
    assert get.annotations.read_only_hint is True
    assert cancel.annotations.destructive_hint is True


def test_error_result_maps_to_content_and_link():
    link = {'name': 'narracion.wav', 'uri': 'file:///C:/out/narracion.wav', 'mime_type': 'audio/wav'}
    result = ToolResult(
        text='No existe el archivo.',
        structured={'error': {'code': 'input_not_found', 'params': {}, 'message': 'No existe el archivo.'}},
        is_error=True,
        links=[link],
    )
    call = sdk._call_result(types, result)
    assert call.is_error is True
    assert call.structured_content == result.structured
    assert [type(item) for item in call.content] == [types.TextContent, types.ResourceLink]
    assert str(call.content[1].uri).startswith('file:///')

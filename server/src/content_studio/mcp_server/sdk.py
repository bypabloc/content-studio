"""Publicación por el protocolo MCP con el SDK `mcp` (spec 029, D-1).

El SDK se importa dentro de las funciones: `studio` sin `mcp` sigue arrancando, y `tools.py` no lo necesita.
"""

from __future__ import annotations

import importlib.metadata
from typing import Any

from content_studio.mcp_server import catalog
from content_studio.mcp_server.bridge import Bridge, Notify, ToolResult

SERVER_NAME = 'content-studio'
INSTRUCTIONS = (
    'Local content-studio tools: narrate text, make background music, transcribe, analyze silences and convert media. '
    'Jobs are queued on the shared server: call studio_wait_job to get the output file paths.'
)


def build_server(bridge: Bridge) -> Any:
    """El servidor MCP de bajo nivel con las herramientas de `catalog.TOOLS` y el puente detrás."""
    from mcp import types
    from mcp.server import Server

    async def on_list_tools(ctx: Any, params: Any) -> Any:  # noqa: ARG001
        return types.ListToolsResult(tools=[_tool(types, definition) for definition in catalog.TOOLS])

    async def on_call_tool(ctx: Any, params: Any) -> Any:
        token = (ctx.meta or {}).get('progress_token')
        notify = _notifier(ctx, token) if token is not None else None
        result = await bridge.call(params.name, params.arguments or {}, notify)
        return _call_result(types, result)

    return Server(
        SERVER_NAME,
        version=_version(),
        instructions=INSTRUCTIONS,
        on_list_tools=on_list_tools,
        on_call_tool=on_call_tool,
    )


async def serve_stdio(server: Any) -> None:
    """Atiende un cliente por stdin y stdout hasta que cierra."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def _tool(types: Any, definition: catalog.ToolDef) -> Any:
    return types.Tool(
        name=definition.name,
        title=definition.title,
        description=definition.description,
        input_schema=definition.input_schema,
        output_schema=definition.output_schema,
        annotations=types.ToolAnnotations(
            title=definition.title,
            read_only_hint=definition.read_only,
            destructive_hint=definition.destructive,
        ),
    )


def _call_result(types: Any, result: ToolResult) -> Any:
    content = [types.TextContent(type='text', text=result.text)]
    content += [
        types.ResourceLink(name=link['name'], uri=link['uri'], mime_type=link['mime_type']) for link in result.links
    ]
    return types.CallToolResult(content=content, structured_content=result.structured, is_error=result.is_error)


def _notifier(ctx: Any, token: Any) -> Notify:
    async def notify(progress: float, total: float | None, message: str | None) -> None:
        await ctx.session.send_progress_notification(token, progress=progress, total=total, message=message)

    return notify


def _version() -> str:
    try:
        return importlib.metadata.version('content-studio')
    except importlib.metadata.PackageNotFoundError:
        return '0.0.0'

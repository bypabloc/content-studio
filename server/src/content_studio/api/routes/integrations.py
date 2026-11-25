"""GET /integrations/mcp-config: el fragmento MCP de un cliente para Ajustes > Integraciones (spec 029)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from content_studio.mcp_server.config import ClientName, fragment, launch_command

router = APIRouter(prefix='/integrations')


class McpConfigOut(BaseModel):
    """El fragmento de un cliente: el archivo de configuración que pega el usuario."""

    client: ClientName
    fragment: str


@router.get('/mcp-config', response_model=McpConfigOut)
def mcp_config(client: ClientName) -> McpConfigOut:
    """El fragmento de `client` con el comando de `studio mcp` de esta instalación."""
    return McpConfigOut(client=client, fragment=fragment(client, launch_command()))

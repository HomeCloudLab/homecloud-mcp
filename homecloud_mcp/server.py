"""stdio MCP server entry."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from homecloud_mcp.core.client import build_client
from homecloud_mcp.core.errors import tool_error_payload
from homecloud_mcp.core.registry import ModuleRegistry
from homecloud_mcp.modules import build_registry

logger = logging.getLogger(__name__)

SERVER_NAME = "homecloud-mcp"
SERVER_VERSION = "0.1.0"


def create_server(registry: ModuleRegistry) -> Server:
    app = Server(SERVER_NAME)

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return registry.list_tools()

    @app.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
        try:
            result = registry.call_tool(name, arguments)
            text = json.dumps(result, default=str, ensure_ascii=False)
            return [types.TextContent(type="text", text=text)]
        except Exception as exc:
            logger.exception("tool %s failed", name)
            payload = tool_error_payload(exc)
            return [types.TextContent(type="text", text=json.dumps(payload))]

    return app


async def run_async(registry: ModuleRegistry | None = None) -> None:
    reg = registry or build_registry(build_client())
    app = create_server(reg)
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(run_async())


if __name__ == "__main__":
    main()

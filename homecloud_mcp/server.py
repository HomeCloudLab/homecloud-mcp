"""stdio MCP server entry."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from homecloud_mcp import __version__
from homecloud_mcp.core.client import build_client
from homecloud_mcp.core.errors import tool_error_payload
from homecloud_mcp.core.registry import ModuleRegistry
from homecloud_mcp.modules import build_registry

logger = logging.getLogger(__name__)

SERVER_NAME = "homecloud-mcp"
SERVER_VERSION = __version__
SERVER_TITLE = "HomeCloud"
SERVER_DESCRIPTION = (
    "HomeCloud platform MCP — Tasks today; more services via the same registry."
)
SERVER_INSTRUCTIONS = """\
HomeCloud console/control-plane tools for the signed-in account (SDK profile / Access Key).

Prefer compact tool responses (default). Use fields=… only when you need extra keys.
Tasks keys look like TASK-12 or a numeric sequence. Assignees accept usernames or "me".
Destructive tools require confirm=true. Bulk create with external_id upserts (safe retries).
For list pagination use cursor with sort=-sequence or ±created_at.
"""
SERVER_WEBSITE = "https://console.holab.abrdns.com"


def create_server(registry: ModuleRegistry) -> Server:
    async def on_list_tools(
        _ctx: Any, _params: types.PaginatedRequestParams | None
    ) -> types.ListToolsResult:
        return types.ListToolsResult(tools=registry.list_tools())

    async def on_call_tool(
        _ctx: Any, params: types.CallToolRequestParams
    ) -> types.CallToolResult:
        try:
            # Sync SDK would block the event loop; run tools in a worker thread.
            result = await asyncio.to_thread(
                registry.call_tool, params.name, params.arguments or {}
            )
            text = json.dumps(result, default=str, ensure_ascii=False)
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=text)]
            )
        except Exception as exc:
            logger.exception("tool %s failed", params.name)
            payload = tool_error_payload(exc)
            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text", text=json.dumps(payload, ensure_ascii=False)
                    )
                ],
                isError=True,
            )

    return Server(
        SERVER_NAME,
        version=SERVER_VERSION,
        title=SERVER_TITLE,
        description=SERVER_DESCRIPTION,
        instructions=SERVER_INSTRUCTIONS,
        website_url=SERVER_WEBSITE,
        on_list_tools=on_list_tools,
        on_call_tool=on_call_tool,
    )


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

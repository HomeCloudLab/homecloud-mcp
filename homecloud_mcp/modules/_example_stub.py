"""
Example service module stub — not registered by default.

Copy this file, implement ``list_tools`` / ``call_tool``, and add your class
to ``default_modules()`` in ``modules/__init__.py``.

Tool names should be prefixed with the service id, e.g. ``compute_list_machines``.
"""

from __future__ import annotations

from typing import Any

from homecloud_mcp.core.registry import ToolDefinition
from homecloud_sdk import HomeCloudClient


class ExampleComputeModule:
    """Placeholder for a future Compute module."""

    name = "compute"

    def __init__(self, client: HomeCloudClient) -> None:
        self._client = client

    def list_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="compute_ping",
                description="Stub — returns ok when Compute module is wired up.",
                input_schema={"type": "object", "properties": {}},
                read_only=True,
            )
        ]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if name == "compute_ping":
            return {"ok": True, "module": self.name}
        raise KeyError(name)

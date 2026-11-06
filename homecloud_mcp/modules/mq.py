"""MQ (Message Queues) module — control-plane list/get via homecloud-sdk."""

from __future__ import annotations

from typing import Any

from homecloud_sdk import HomeCloudClient

from homecloud_mcp.core.registry import ToolDefinition

_OBJ = {"type": "object"}
_STR = {"type": "string"}
_BOOL = {"type": "boolean"}


class MqModule:
    name = "mq"

    def __init__(self, client: HomeCloudClient) -> None:
        self._client = client
        self._queues = client.queues

    def list_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="mq_list_queues",
                title="List MQ queues",
                description="List Message Queue definitions (control plane; JWT or Access Key SigV1).",
                input_schema={
                    **_OBJ,
                    "properties": {
                        "live": {
                            **_BOOL,
                            "description": "Include live depth/inflight/DLQ stats",
                        },
                    },
                },
                read_only=True,
                idempotent=True,
            ),
            ToolDefinition(
                name="mq_get_queue",
                title="Get MQ queue",
                description="Get one queue by name (control plane).",
                input_schema={
                    **_OBJ,
                    "properties": {
                        "queue_name": {**_STR, "description": "Queue name"},
                    },
                    "required": ["queue_name"],
                },
                read_only=True,
                idempotent=True,
            ),
        ]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if name == "mq_list_queues":
            items = self._queues.list(live=bool(arguments.get("live", False)))
            return {"total": len(items), "items": items, "live": bool(arguments.get("live", False))}
        if name == "mq_get_queue":
            queue = str(arguments.get("queue_name") or "").strip()
            if not queue:
                raise ValueError("queue_name is required")
            return self._queues.get(queue)
        raise KeyError(name)

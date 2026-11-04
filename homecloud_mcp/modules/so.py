"""SO (Object Storage) module — read-only list tools via homecloud-sdk."""

from __future__ import annotations

from typing import Any

from homecloud_sdk import HomeCloudClient

from homecloud_mcp.core.registry import ToolDefinition

_OBJ = {"type": "object"}
_STR = {"type": "string"}
_BOOL = {"type": "boolean"}
_INT = {"type": "integer"}


class SoModule:
    name = "so"

    def __init__(self, client: HomeCloudClient) -> None:
        self._client = client
        self._so = client.so

    def list_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="so_list_buckets",
                title="List SO buckets",
                description="List Object Storage buckets for the configured account (SOReadOnly: so:ListBuckets).",
                input_schema={**_OBJ, "properties": {}},
                read_only=True,
                idempotent=True,
            ),
            ToolDefinition(
                name="so_list_objects",
                title="List SO objects",
                description=(
                    "List objects in a bucket (data plane; Access Key required). "
                    "Supports prefix and pagination."
                ),
                input_schema={
                    **_OBJ,
                    "properties": {
                        "bucket": {**_STR, "description": "Bucket name"},
                        "prefix": {**_STR, "description": "Key prefix filter"},
                        "recursive": {**_BOOL, "description": "List recursively under prefix"},
                        "page_size": {**_INT, "description": "Page size (default 100)"},
                        "continuation_token": {
                            **_STR,
                            "description": "Continuation token from a prior response",
                        },
                    },
                    "required": ["bucket"],
                },
                read_only=True,
                idempotent=True,
            ),
        ]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if name == "so_list_buckets":
            items = self._so.list_buckets()
            return {
                "total": len(items),
                "items": [
                    {
                        "name": item.get("name"),
                        "managed": item.get("managed"),
                        "managed_kind": item.get("managed_kind"),
                    }
                    for item in items
                ],
            }
        if name == "so_list_objects":
            bucket = str(arguments.get("bucket") or "").strip()
            if not bucket:
                raise ValueError("bucket is required")
            return self._so.list_objects(
                bucket,
                prefix=str(arguments.get("prefix") or ""),
                recursive=bool(arguments.get("recursive", False)),
                page_size=int(arguments.get("page_size") or 100),
                continuation_token=arguments.get("continuation_token"),
            )
        raise KeyError(name)

"""Register enabled service modules (Tasks first; add more here)."""

from __future__ import annotations

from collections.abc import Iterable

from homecloud_mcp.core.registry import ModuleRegistry, ServiceModule
from homecloud_sdk import HomeCloudClient

# Remote MCP Tasks surface (cloud-api Streamable HTTP).
REMOTE_TASKS_TOOLS: frozenset[str] = frozenset(
    {
        "tasks_search",
        "tasks_get",
        "tasks_schema",
        "tasks_people_list",
        "tasks_create",
        "tasks_update",
        "tasks_transition",
        "tasks_bulk_upsert",
        "tasks_bulk_delete",
        "tasks_comment",
        "tasks_label",
        "tasks_link",
        "tasks_delete",
        "tasks_activity",
        "tasks_comment_file_url",
        "tasks_comment_update",
        "tasks_comment_delete",
        "tasks_archive",
        "tasks_restore",
        "tasks_watch",
        "tasks_unwatch",
        "tasks_relations",
        "tasks_unlink",
        "tasks_labels_list",
        "tasks_share",
        "tasks_projects",
    }
)
# Back-compat alias
REMOTE_WAVE1_TOOLS = REMOTE_TASKS_TOOLS

REMOTE_SO_MQ_TOOLS: frozenset[str] = frozenset(
    {
        "so_list_buckets",
        "so_list_objects",
        "mq_list_queues",
        "mq_get_queue",
    }
)


def default_modules(client: HomeCloudClient) -> list[ServiceModule]:
    from homecloud_mcp.modules.mq import MqModule
    from homecloud_mcp.modules.so import SoModule
    from homecloud_mcp.modules.tasks import TasksModule

    return [TasksModule(client), SoModule(client), MqModule(client)]


def build_registry(
    client: HomeCloudClient,
    *,
    include_tools: Iterable[str] | None = None,
) -> ModuleRegistry:
    """Build the module registry.

    ``include_tools`` — when set, only those tool names are registered (Wave 1 Remote).
    """
    allow = frozenset(include_tools) if include_tools is not None else None
    registry = ModuleRegistry()
    for module in default_modules(client):
        if allow is None:
            registry.register(module)
            continue
        tools = [t for t in module.list_tools() if t.name in allow]
        if not tools:
            continue
        registry.register(_FilteredModule(module, tools))
    return registry


class _FilteredModule:
    """Expose a subset of another module's tools without duplicating handlers."""

    def __init__(self, inner: ServiceModule, tools: list) -> None:
        self.name = inner.name
        self._inner = inner
        self._tools = tools
        self._names = {t.name for t in tools}

    def list_tools(self):
        return list(self._tools)

    def call_tool(self, name: str, arguments: dict):
        if name not in self._names:
            raise KeyError(f"unknown tool: {name}")
        return self._inner.call_tool(name, arguments)

"""Register enabled service modules (Tasks first; add more here)."""

from __future__ import annotations

from homecloud_mcp.core.registry import ModuleRegistry, ServiceModule
from homecloud_sdk import HomeCloudClient


def default_modules(client: HomeCloudClient) -> list[ServiceModule]:
    from homecloud_mcp.modules.tasks import TasksModule

    return [TasksModule(client)]


def build_registry(client: HomeCloudClient) -> ModuleRegistry:
    registry = ModuleRegistry()
    for module in default_modules(client):
        registry.register(module)
    return registry

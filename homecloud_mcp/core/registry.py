"""Service module registry — core has no service-specific imports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

import mcp.types as types


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]
    read_only: bool = False
    destructive: bool = False
    idempotent: bool = False
    """Human title shown in MCP clients (Cursor / Claude), like Atlassian tools."""
    title: str | None = None

    def to_mcp_tool(self) -> types.Tool:
        annotations = types.ToolAnnotations(
            title=self.title or self.name.replace("_", " ").title(),
            readOnlyHint=True if self.read_only else None,
            destructiveHint=True if self.destructive else None,
            idempotentHint=True if self.idempotent else None,
        )
        return types.Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.input_schema,
            annotations=annotations,
        )


@runtime_checkable
class ServiceModule(Protocol):
    """One HomeCloud service surface (Tasks, SO, MQ, …)."""

    name: str

    def list_tools(self) -> list[ToolDefinition]:
        ...

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        ...


class ModuleRegistry:
    def __init__(self) -> None:
        self._modules: dict[str, ServiceModule] = {}
        self._tool_owner: dict[str, ServiceModule] = {}

    def register(self, module: ServiceModule) -> None:
        if module.name in self._modules:
            raise ValueError(f"module already registered: {module.name}")
        self._modules[module.name] = module
        for tool in module.list_tools():
            if tool.name in self._tool_owner:
                raise ValueError(f"duplicate tool name: {tool.name}")
            self._tool_owner[tool.name] = module

    def list_tools(self) -> list[types.Tool]:
        tools: list[types.Tool] = []
        for module in self._modules.values():
            for spec in module.list_tools():
                tools.append(spec.to_mcp_tool())
        return tools

    def call_tool(self, name: str, arguments: dict[str, Any] | None) -> Any:
        module = self._tool_owner.get(name)
        if module is None:
            raise KeyError(f"unknown tool: {name}")
        return module.call_tool(name, arguments or {})

from homecloud_mcp.core.registry import ModuleRegistry, ToolDefinition


class DummyModule:
    name = "dummy"

    def list_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="dummy_echo",
                description="echo",
                input_schema={"type": "object", "properties": {"x": {"type": "string"}}},
                read_only=True,
            )
        ]

    def call_tool(self, name: str, arguments: dict) -> dict:
        if name == "dummy_echo":
            return {"x": arguments.get("x")}
        raise KeyError(name)


def test_registry_registers_non_tasks_module() -> None:
    reg = ModuleRegistry()
    reg.register(DummyModule())
    names = [t.name for t in reg.list_tools()]
    assert names == ["dummy_echo"]
    assert reg.call_tool("dummy_echo", {"x": "hi"}) == {"x": "hi"}

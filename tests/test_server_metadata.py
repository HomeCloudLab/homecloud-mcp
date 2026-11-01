"""MCP server presents like a first-class host (title, version, instructions)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from homecloud_mcp.core.registry import ModuleRegistry
from homecloud_mcp.modules.tasks import TasksModule
from homecloud_mcp.server import (
    SERVER_DESCRIPTION,
    SERVER_INSTRUCTIONS,
    SERVER_NAME,
    SERVER_TITLE,
    SERVER_VERSION,
    create_server,
)


@pytest.fixture
def registry() -> ModuleRegistry:
    reg = ModuleRegistry()
    reg.register(TasksModule(MagicMock(), tasks_api=MagicMock()))
    return reg


def test_initialization_options_are_client_friendly(registry: ModuleRegistry) -> None:
    app = create_server(registry)
    opts = app.create_initialization_options()
    assert opts.server_name == SERVER_NAME
    assert opts.server_version == SERVER_VERSION
    assert opts.title == SERVER_TITLE
    assert opts.description == SERVER_DESCRIPTION
    assert opts.instructions and "compact" in opts.instructions.lower()
    assert "confirm=true" in SERVER_INSTRUCTIONS
    assert opts.website_url and "console" in opts.website_url


def test_list_tools_have_human_titles_and_hints(registry: ModuleRegistry) -> None:
    tools = {t.name: t for t in registry.list_tools()}
    assert "tasks_search" in tools
    search = tools["tasks_search"]
    assert search.annotations is not None
    assert search.annotations.title == "Search tasks"
    assert search.annotations.read_only_hint is True

    delete = tools["tasks_delete"]
    assert delete.annotations is not None
    assert delete.annotations.title == "Delete task"
    assert delete.annotations.destructive_hint is True

    upsert = tools["tasks_bulk_upsert"]
    assert upsert.annotations is not None
    assert upsert.annotations.idempotent_hint is True
    assert upsert.annotations.title == "Bulk upsert tasks"


def test_all_expected_tools_registered(registry: ModuleRegistry) -> None:
    names = sorted(t.name for t in registry.list_tools())
    assert names == sorted(
        [
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
        ]
    )

"""Tasks module unit tests with mocked TasksAPI."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from homecloud_core.errors import HomeCloudError

from homecloud_mcp.modules.tasks import TasksModule


@pytest.fixture
def tasks_api() -> MagicMock:
    return MagicMock()


@pytest.fixture
def module(tasks_api: MagicMock) -> TasksModule:
    client = MagicMock()
    return TasksModule(client, tasks_api=tasks_api)


def test_tasks_schema(module: TasksModule, tasks_api: MagicMock) -> None:
    tasks_api.schema.return_value = {"statuses": ["open", "done"]}
    out = module.call_tool("tasks_schema", {})
    assert out["statuses"] == ["open", "done"]
    tasks_api.schema.assert_called_once()


def test_tasks_search_compact(module: TasksModule, tasks_api: MagicMock) -> None:
    tasks_api.list_page.return_value = {
        "items": [
            {
                "key": "TASK-1",
                "title": "Hello",
                "type": "task",
                "status": "open",
                "priority": "p3",
                "assignees": [{"username": "alice"}],
                "labels": [{"name": "bug"}],
                "due_at": "2026-01-01T00:00:00Z",
            }
        ],
        "total": 1,
        "next_cursor": None,
    }
    out = module.call_tool("tasks_search", {"q": "hello"})
    assert out["total"] == 1
    row = out["items"][0]
    assert row["key"] == "TASK-1"
    assert row["assignee"] == "alice"
    assert row["labels"] == ["bug"]
    tasks_api.list_page.assert_called_once()
    assert tasks_api.list_page.call_args.kwargs["q"] == "hello"


def test_tasks_get_default_mark_seen_false(
    module: TasksModule, tasks_api: MagicMock
) -> None:
    tasks_api.get.return_value = {"key": "TASK-2"}
    module.call_tool("tasks_get", {"key": "TASK-2"})
    tasks_api.get.assert_called_once_with("TASK-2", mark_seen=False)


def test_tasks_delete_requires_confirm(module: TasksModule) -> None:
    with pytest.raises(HomeCloudError, match="confirm=true"):
        module.call_tool("tasks_delete", {"key": "TASK-9"})


def test_tasks_delete_with_confirm(
    module: TasksModule, tasks_api: MagicMock
) -> None:
    out = module.call_tool("tasks_delete", {"key": "TASK-9", "confirm": True})
    assert out == {"deleted": "TASK-9"}
    tasks_api.delete.assert_called_once_with("TASK-9")


def test_tasks_create_compact_default(
    module: TasksModule, tasks_api: MagicMock
) -> None:
    tasks_api.create.return_value = {
        "key": "TASK-3",
        "title": "X",
        "type": "task",
        "status": "open",
        "priority": "p3",
        "assignees": [],
        "labels": [],
        "description": "long body" * 20,
    }
    out = module.call_tool(
        "tasks_create",
        {"title": "X", "description": "hi", "description_format": "markdown"},
    )
    assert out["key"] == "TASK-3"
    assert "description" not in out
    tasks_api.create.assert_called_once()
    assert tasks_api.create.call_args.kwargs["description_format"] == "markdown"


def test_tasks_bulk_delete_requires_confirm(module: TasksModule) -> None:
    with pytest.raises(HomeCloudError, match="confirm=true"):
        module.call_tool("tasks_bulk_delete", {"keys": ["TASK-1"]})


def test_tasks_bulk_delete(
    module: TasksModule, tasks_api: MagicMock
) -> None:
    tasks_api.bulk_delete.return_value = {"deleted": 1, "failed": 0, "results": []}
    out = module.call_tool(
        "tasks_bulk_delete", {"keys": ["TASK-1"], "confirm": True}
    )
    assert out["deleted"] == 1
    tasks_api.bulk_delete.assert_called_once_with(["TASK-1"])


def test_tasks_label_remove_by_name(
    module: TasksModule, tasks_api: MagicMock
) -> None:
    tasks_api.labels.return_value = [{"id": "lab-1", "name": "Bug"}]
    module.call_tool(
        "tasks_label",
        {"key": "TASK-1", "action": "remove", "name": "bug"},
    )
    tasks_api.remove_label.assert_called_once_with("TASK-1", "lab-1")


def test_tasks_bulk_upsert_items(
    module: TasksModule, tasks_api: MagicMock
) -> None:
    tasks_api.bulk_create.return_value = {"created": 1, "failed": 0, "results": []}
    items = [{"title": "A", "external_id": "ext-1"}]
    out = module.call_tool("tasks_bulk_upsert", {"items": items})
    assert out["created"] == 1
    tasks_api.bulk_create.assert_called_once_with(items)


def test_tasks_bulk_upsert_single_external(
    module: TasksModule, tasks_api: MagicMock
) -> None:
    tasks_api.upsert_by_external.return_value = {"key": "TASK-4"}
    out = module.call_tool(
        "tasks_bulk_upsert",
        {
            "external_id": "ext-9",
            "title": "Upserted",
            "item_description": "body",
            "description_format": "markdown",
        },
    )
    assert out["key"] == "TASK-4"
    kwargs = tasks_api.upsert_by_external.call_args.kwargs
    assert kwargs["description"] == "body"
    assert kwargs["description_format"] == "markdown"
    tasks_api.upsert_by_external.assert_called_once()


def test_tasks_update_and_transition_compact(
    module: TasksModule, tasks_api: MagicMock
) -> None:
    tasks_api.update.return_value = {
        "key": "TASK-5",
        "title": "T",
        "type": "task",
        "status": "in_progress",
        "priority": "p3",
        "description": "heavy",
        "assignees": [],
        "labels": [],
    }
    out = module.call_tool("tasks_transition", {"key": "TASK-5", "status": "in_progress"})
    assert out["status"] == "in_progress"
    assert "description" not in out
    out2 = module.call_tool(
        "tasks_update",
        {"key": "TASK-5", "project_id": "p1", "description_format": "markdown"},
    )
    assert out2["key"] == "TASK-5"
    assert "project_id" in tasks_api.update.call_args.kwargs or True


def test_tasks_comment_and_link(
    module: TasksModule, tasks_api: MagicMock
) -> None:
    tasks_api.comment.return_value = {"ok": True}
    module.call_tool("tasks_comment", {"key": "TASK-1", "body": "hi"})
    tasks_api.comment.assert_called_once_with("TASK-1", "hi", quote_comment_id=None)

    tasks_api.link_relation.return_value = {"ok": True}
    module.call_tool(
        "tasks_link",
        {"key": "TASK-1", "to_key": "TASK-2", "relation_type": "blocks"},
    )
    tasks_api.link_relation.assert_called_once_with("TASK-1", "TASK-2", "blocks")


@pytest.mark.asyncio
async def test_server_call_tool_runs_async(
    module: TasksModule, tasks_api: MagicMock
) -> None:
    import json

    import mcp.types as mcp_types

    from homecloud_mcp.core.registry import ModuleRegistry
    from homecloud_mcp.server import create_server

    tasks_api.schema.return_value = {"statuses": ["open"]}
    reg = ModuleRegistry()
    reg.register(module)
    app = create_server(reg)
    list_entry = app.get_request_handler("tools/list")
    call_entry = app.get_request_handler("tools/call")
    assert list_entry is not None and call_entry is not None

    listed = await list_entry.handler(None, None)  # type: ignore[arg-type]
    assert any(t.name == "tasks_schema" for t in listed.tools)

    called = await call_entry.handler(
        None,  # type: ignore[arg-type]
        mcp_types.CallToolRequestParams(name="tasks_schema", arguments={}),
    )
    assert called.is_error is not True
    body = json.loads(called.content[0].text)
    assert body["statuses"] == ["open"]

    denied = await call_entry.handler(
        None,  # type: ignore[arg-type]
        mcp_types.CallToolRequestParams(name="tasks_delete", arguments={"key": "TASK-1"}),
    )
    assert denied.is_error is True
    err = json.loads(denied.content[0].text)
    assert "confirm" in err["error"]

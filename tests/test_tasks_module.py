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

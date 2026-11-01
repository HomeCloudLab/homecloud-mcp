"""Error shaping + compact payload size (speed / token budget)."""

from __future__ import annotations

from homecloud_core.errors import HomeCloudError

from homecloud_mcp.core.compact import compact_task_summary
from homecloud_mcp.core.errors import tool_error_payload


def test_tool_error_includes_details_and_status() -> None:
    exc = HomeCloudError("bad sort")
    exc.code = "tasks.invalid_sort"
    exc.status_code = 400
    exc.details = {"allowed": ["sequence", "created_at"]}
    payload = tool_error_payload(exc)
    assert payload["code"] == "tasks.invalid_sort"
    assert payload["status"] == 400
    assert payload["details"]["allowed"] == ["sequence", "created_at"]


def test_tool_error_unknown_is_internal() -> None:
    payload = tool_error_payload(RuntimeError("boom"))
    assert payload == {"error": "boom", "code": "internal_error"}


def test_compact_summary_drops_heavy_fields() -> None:
    fat = {
        "key": "TASK-9",
        "title": "Rotate cert",
        "type": "task",
        "status": "open",
        "priority": "p2",
        "external_id": "jira:ABC-1",
        "description": "x" * 5000,
        "description_format": "markdown",
        "assignees": [{"username": "alice", "email": "a@x"}, {"username": "bob"}],
        "labels": [{"name": "ops", "color": "#fff"}, {"name": "sec"}],
        "due_at": "2026-01-01T00:00:00Z",
        "watchers": [{"username": "carol"}] * 20,
        "resources": [{"resource_type": "so", "resource_id": "b"}] * 10,
        "custom_fields": {"a": 1},
    }
    slim = compact_task_summary(fat)
    assert "description" not in slim
    assert "watchers" not in slim
    assert "resources" not in slim
    assert slim["assignee"] == "alice, bob"
    assert slim["labels"] == ["ops", "sec"]
    assert len(str(slim)) < len(str(fat)) // 5

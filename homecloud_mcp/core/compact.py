"""Optional field projection for smaller tool payloads."""

from __future__ import annotations

from typing import Any


def pick_fields(obj: dict[str, Any], fields: list[str] | None) -> dict[str, Any]:
    if not fields:
        return obj
    return {k: obj[k] for k in fields if k in obj}


def compact_task_summary(item: dict[str, Any]) -> dict[str, Any]:
    assignees = item.get("assignees") or (
        [] if not item.get("assignee") else [item["assignee"]]
    )
    names = [
        a.get("username")
        for a in assignees
        if isinstance(a, dict) and a.get("username")
    ]
    labels = item.get("labels") or []
    label_names = [
        lb.get("name") for lb in labels if isinstance(lb, dict) and lb.get("name")
    ]
    return {
        "key": item.get("key"),
        "title": item.get("title"),
        "type": item.get("type"),
        "status": item.get("status"),
        "priority": item.get("priority"),
        "external_id": item.get("external_id"),
        "assignee": ", ".join(names) if names else None,
        "labels": label_names or None,
        "due_at": item.get("due_at"),
    }


def apply_fields(data: Any, fields: list[str] | None) -> Any:
    if fields is None:
        return data
    if isinstance(data, dict):
        return pick_fields(data, fields)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return [pick_fields(row, fields) for row in data]
    return data

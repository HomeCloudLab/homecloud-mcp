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


def task_card_markdown(item: dict[str, Any], *, console_base: str | None = None) -> str:
    """Jira-like markdown card for MCP hosts that render markdown tool results."""
    summary = compact_task_summary(item)
    key = summary.get("key") or "?"
    title = summary.get("title") or "(no title)"
    status = summary.get("status") or "—"
    priority = summary.get("priority") or "—"
    assignee = summary.get("assignee") or "—"
    labels = summary.get("labels") or []
    label_txt = ", ".join(labels) if labels else "—"
    base = (console_base or "https://console.holab.abrdns.com").rstrip("/")
    link = f"{base}/console/tasks/{key}"
    return (
        f"### {key} — {title}\n\n"
        f"| | |\n|---|---|\n"
        f"| **Status** | `{status}` |\n"
        f"| **Priority** | `{priority}` |\n"
        f"| **Assignee** | {assignee} |\n"
        f"| **Labels** | {label_txt} |\n\n"
        f"[Open in HomeCloud]({link})"
    )


def apply_fields(data: Any, fields: list[str] | None) -> Any:
    if fields is None:
        return data
    if isinstance(data, dict):
        return pick_fields(data, fields)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return [pick_fields(row, fields) for row in data]
    return data

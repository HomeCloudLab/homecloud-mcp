"""Tasks service module — ``tasks_*`` MCP tools via homecloud-sdk."""

from __future__ import annotations

from typing import Any

from homecloud_core.errors import HomeCloudError
from homecloud_sdk import HomeCloudClient
from homecloud_sdk.services import TasksAPI

from homecloud_mcp.core.compact import apply_fields, compact_task_summary
from homecloud_mcp.core.registry import ToolDefinition

_OBJ = {"type": "object"}
_STR = {"type": "string"}
_BOOL = {"type": "boolean"}
_ARR = {"type": "array"}


class TasksModule:
    name = "tasks"

    def __init__(self, client: HomeCloudClient, tasks_api: TasksAPI | None = None) -> None:
        self._client = client
        self._tasks = tasks_api if tasks_api is not None else client.tasks

    def list_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="tasks_search",
                description=(
                    "Search/list task items (console ``q`` grammar: @user, &label, "
                    "#service/resource, type:, due:, …)."
                ),
                input_schema={
                    **_OBJ,
                    "properties": {
                        "q": {"type": "string", "description": "Smart search query"},
                        "type": _STR,
                        "status": _STR,
                        "assignee": _STR,
                        "label": _STR,
                        "project_id": _STR,
                        "due": _STR,
                        "archived": _BOOL,
                        "external_id": _STR,
                        "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                        "cursor": _STR,
                        "sort": _STR,
                        "compact": {
                            "type": "boolean",
                            "description": "If true (default), return slim rows",
                            "default": True,
                        },
                        "fields": {
                            "type": "array",
                            "items": _STR,
                            "description": "Project each item to these keys",
                        },
                    },
                },
                read_only=True,
            ),
            ToolDefinition(
                name="tasks_get",
                description="Fetch one task by key. Default mark_seen=false (read-only).",
                input_schema={
                    **_OBJ,
                    "properties": {
                        "key": {**_STR, "description": "Task key, e.g. TASK-12"},
                        "mark_seen": {
                            "type": "boolean",
                            "description": "When true, marks discussion seen (write)",
                            "default": False,
                        },
                        "fields": {"type": "array", "items": _STR},
                    },
                    "required": ["key"],
                },
                read_only=True,
            ),
            ToolDefinition(
                name="tasks_schema",
                description="Valid types, statuses, priorities, and transitions.",
                input_schema={**_OBJ, "properties": {}},
                read_only=True,
            ),
            ToolDefinition(
                name="tasks_people_list",
                description="List account users for assignee resolution (@username, me).",
                input_schema={**_OBJ, "properties": {}},
                read_only=True,
            ),
            ToolDefinition(
                name="tasks_create",
                description="Create a task item.",
                input_schema={
                    **_OBJ,
                    "properties": {
                        "title": _STR,
                        "type": {"type": "string", "default": "task"},
                        "description": _STR,
                        "status": _STR,
                        "external_id": _STR,
                        "assignees": {"type": "array", "items": _STR},
                        "due_at": _STR,
                        "project_id": _STR,
                        "priority": _STR,
                        "label_names": {"type": "array", "items": _STR},
                        "parent_key": _STR,
                    },
                    "required": ["title"],
                },
            ),
            ToolDefinition(
                name="tasks_update",
                description="Patch fields on a task (assignees accept usernames / me).",
                input_schema={
                    **_OBJ,
                    "properties": {
                        "key": _STR,
                        "title": _STR,
                        "description": _STR,
                        "status": _STR,
                        "priority": _STR,
                        "assignees": {"type": "array", "items": _STR},
                        "due_at": _STR,
                        "label_names": {"type": "array", "items": _STR},
                        "clear_assignee": _BOOL,
                    },
                    "required": ["key"],
                },
            ),
            ToolDefinition(
                name="tasks_transition",
                description="Change task status (validated by workflow on the API).",
                input_schema={
                    **_OBJ,
                    "properties": {"key": _STR, "status": _STR},
                    "required": ["key", "status"],
                },
            ),
            ToolDefinition(
                name="tasks_bulk_upsert",
                description=(
                    "Bulk create items, or upsert one item by external_id "
                    "(pass either ``items`` or ``external_id`` + fields)."
                ),
                input_schema={
                    **_OBJ,
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Batch for POST …/items/bulk",
                        },
                        "external_id": _STR,
                        "title": _STR,
                        "type": _STR,
                        "item_description": {
                            "type": "string",
                            "description": "Task description body",
                        },
                        "status": _STR,
                        "assignees": {"type": "array", "items": _STR},
                    },
                },
            ),
            ToolDefinition(
                name="tasks_comment",
                description="Add a comment to a task.",
                input_schema={
                    **_OBJ,
                    "properties": {
                        "key": _STR,
                        "body": _STR,
                        "quote_comment_id": _STR,
                    },
                    "required": ["key", "body"],
                },
            ),
            ToolDefinition(
                name="tasks_label",
                description="Add or remove a label on a task.",
                input_schema={
                    **_OBJ,
                    "properties": {
                        "key": _STR,
                        "action": {
                            "type": "string",
                            "enum": ["add", "remove"],
                            "default": "add",
                        },
                        "name": _STR,
                        "color": _STR,
                        "label_id": _STR,
                    },
                    "required": ["key"],
                },
            ),
            ToolDefinition(
                name="tasks_link",
                description="Link a related task or a platform resource.",
                input_schema={
                    **_OBJ,
                    "properties": {
                        "key": _STR,
                        "to_key": _STR,
                        "relation_type": _STR,
                        "resource_type": _STR,
                        "resource_id": _STR,
                        "resource_ref": _STR,
                    },
                    "required": ["key"],
                },
            ),
            ToolDefinition(
                name="tasks_delete",
                description="Permanently delete a task. Requires confirm=true.",
                input_schema={
                    **_OBJ,
                    "properties": {
                        "key": _STR,
                        "confirm": {
                            "type": "boolean",
                            "description": "Must be true to delete",
                            "default": False,
                        },
                    },
                    "required": ["key"],
                },
                destructive=True,
            ),
        ]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        handler = {
            "tasks_search": self._search,
            "tasks_get": self._get,
            "tasks_schema": self._schema,
            "tasks_people_list": self._people_list,
            "tasks_create": self._create,
            "tasks_update": self._update,
            "tasks_transition": self._transition,
            "tasks_bulk_upsert": self._bulk_upsert,
            "tasks_comment": self._comment,
            "tasks_label": self._label,
            "tasks_link": self._link,
            "tasks_delete": self._delete,
        }.get(name)
        if handler is None:
            raise KeyError(name)
        return handler(arguments)

    def _search(self, args: dict[str, Any]) -> Any:
        compact = args.get("compact", True)
        fields = args.get("fields")
        page = self._tasks.list_page(
            type=args.get("type"),
            status=args.get("status"),
            assignee=args.get("assignee"),
            label=args.get("label"),
            project_id=args.get("project_id"),
            q=args.get("q"),
            due=args.get("due"),
            archived=bool(args.get("archived", False)),
            external_id=args.get("external_id"),
            limit=args.get("limit"),
            cursor=args.get("cursor"),
            sort=args.get("sort"),
        )
        items = page.get("items", [])
        if compact and fields is None:
            items = [compact_task_summary(i) for i in items]
        else:
            items = apply_fields(items, fields)
        return {
            "items": items,
            "total": page.get("total"),
            "next_cursor": page.get("next_cursor"),
        }

    def _get(self, args: dict[str, Any]) -> Any:
        key = args["key"]
        mark_seen = bool(args.get("mark_seen", False))
        if mark_seen:
            item = self._tasks.get(key, mark_seen=True)
        else:
            item = self._tasks.get(key, mark_seen=False)
        return apply_fields(item, args.get("fields"))

    def _schema(self, _args: dict[str, Any]) -> Any:
        return self._tasks.schema()

    def _people_list(self, _args: dict[str, Any]) -> Any:
        return {"items": self._tasks.people()}

    def _create(self, args: dict[str, Any]) -> Any:
        payload = {k: v for k, v in args.items() if k != "fields"}
        title = payload.pop("title")
        return self._tasks.create(title, **payload)

    def _update(self, args: dict[str, Any]) -> Any:
        key = args.pop("key")
        return self._tasks.update(key, **args)

    def _transition(self, args: dict[str, Any]) -> Any:
        return self._tasks.update(args["key"], status=args["status"])

    def _bulk_upsert(self, args: dict[str, Any]) -> Any:
        items = args.get("items")
        if items is not None:
            return self._tasks.bulk_create(items)
        external_id = args.get("external_id")
        if not external_id:
            raise HomeCloudError("tasks_bulk_upsert requires items or external_id")
        fields = {
            k: v
            for k, v in args.items()
            if k not in ("items", "external_id") and v is not None
        }
        if "item_description" in fields:
            fields["description"] = fields.pop("item_description")
        return self._tasks.upsert_by_external(external_id, **fields)

    def _comment(self, args: dict[str, Any]) -> Any:
        return self._tasks.comment(
            args["key"],
            args["body"],
            quote_comment_id=args.get("quote_comment_id"),
        )

    def _label(self, args: dict[str, Any]) -> Any:
        key = args["key"]
        action = args.get("action", "add")
        if action == "add":
            name = args.get("name")
            if not name:
                raise HomeCloudError("tasks_label add requires name")
            return self._tasks.add_label(key, name, color=args.get("color"))
        label_id = args.get("label_id")
        if not label_id:
            raise HomeCloudError("tasks_label remove requires label_id")
        return self._tasks.remove_label(key, label_id)

    def _link(self, args: dict[str, Any]) -> Any:
        key = args["key"]
        if args.get("to_key") and args.get("relation_type"):
            return self._tasks.link_relation(
                key, args["to_key"], args["relation_type"]
            )
        if args.get("resource_type") and args.get("resource_id"):
            return self._tasks.link_resource(
                key,
                resource_type=args["resource_type"],
                resource_id=args["resource_id"],
                resource_ref=args.get("resource_ref") or "",
            )
        raise HomeCloudError(
            "tasks_link requires to_key+relation_type or resource_type+resource_id"
        )

    def _delete(self, args: dict[str, Any]) -> Any:
        if not args.get("confirm"):
            raise HomeCloudError("tasks_delete requires confirm=true")
        self._tasks.delete(args["key"])
        return {"deleted": args["key"]}

"""Tasks service module — ``tasks_*`` MCP tools via homecloud-sdk."""

from __future__ import annotations

from typing import Any

from homecloud_core.errors import HomeCloudError
from homecloud_sdk import HomeCloudClient
from homecloud_sdk.services import TasksAPI

from homecloud_mcp.core.compact import apply_fields, compact_task_summary, task_card_markdown
from homecloud_mcp.core.registry import ToolDefinition

_OBJ = {"type": "object"}
_STR = {"type": "string"}
_BOOL = {"type": "boolean"}
_ARR = {"type": "array"}

_TASK_TYPES = ["task", "bug", "epic", "story", "subtask"]
_PRIORITIES = ["p0", "p1", "p2", "p3", "p4"]
_DESC_FORMATS = ["plain", "markdown"]

_BULK_ITEM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": _STR,
        "type": {"type": "string", "enum": _TASK_TYPES},
        "description": _STR,
        "description_format": {"type": "string", "enum": _DESC_FORMATS},
        "status": _STR,
        "external_id": {
            **_STR,
            "description": "When set, bulk create upserts by this id (idempotent retries)",
        },
        "assignees": {"type": "array", "items": _STR},
        "due_at": _STR,
        "project_id": _STR,
        "priority": {"type": "string", "enum": _PRIORITIES},
        "label_names": {"type": "array", "items": _STR},
        "parent_key": _STR,
    },
    "required": ["title"],
}


def _compact_write(item: dict[str, Any], args: dict[str, Any]) -> Any:
    fields = args.get("fields")
    if fields is not None:
        return apply_fields(item, fields)
    if args.get("compact", True):
        return compact_task_summary(item)
    return item


class TasksModule:
    name = "tasks"

    def __init__(self, client: HomeCloudClient, tasks_api: TasksAPI | None = None) -> None:
        self._client = client
        self._tasks = tasks_api if tasks_api is not None else client.tasks

    def list_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="tasks_search", title="Search tasks",
                description=(
                    "Search/list task items (console ``q`` grammar: @user, &label, "
                    "#service/resource, type:, due:, …). Cursor works for sort=-sequence "
                    "and ±created_at."
                ),
                input_schema={
                    **_OBJ,
                    "properties": {
                        "q": {"type": "string", "description": "Smart search query"},
                        "type": {"type": "string", "enum": _TASK_TYPES},
                        "status": _STR,
                        "assignee": _STR,
                        "label": _STR,
                        "project_id": _STR,
                        "due": _STR,
                        "archived": _BOOL,
                        "external_id": _STR,
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 200,
                            "description": "Page size (API max 200)",
                        },
                        "cursor": _STR,
                        "sort": {
                            **_STR,
                            "description": "e.g. -sequence, created_at, -created_at",
                        },
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
                name="tasks_get", title="Get task",
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
                        "compact": {
                            "type": "boolean",
                            "description": "If true, return slim summary",
                            "default": False,
                        },
                        "fields": {"type": "array", "items": _STR},
                    },
                    "required": ["key"],
                },
                read_only=True,
            ),
            ToolDefinition(
                name="tasks_schema", title="Task schema",
                description="Valid types, statuses, priorities, description_formats, and transitions.",
                input_schema={**_OBJ, "properties": {}},
                read_only=True,
            ),
            ToolDefinition(
                name="tasks_people_list", title="List people",
                description="List account users for assignee resolution (@username, me).",
                input_schema={**_OBJ, "properties": {}},
                read_only=True,
            ),
            ToolDefinition(
                name="tasks_create", title="Create task",
                description="Create a task item. Returns a compact summary by default.",
                input_schema={
                    **_OBJ,
                    "properties": {
                        "title": _STR,
                        "type": {"type": "string", "enum": _TASK_TYPES, "default": "task"},
                        "description": _STR,
                        "description_format": {
                            "type": "string",
                            "enum": _DESC_FORMATS,
                            "description": "plain or markdown (default plain unless set)",
                        },
                        "status": _STR,
                        "external_id": _STR,
                        "assignees": {"type": "array", "items": _STR},
                        "due_at": _STR,
                        "project_id": _STR,
                        "priority": {"type": "string", "enum": _PRIORITIES},
                        "label_names": {"type": "array", "items": _STR},
                        "parent_key": _STR,
                        "compact": {
                            "type": "boolean",
                            "default": True,
                            "description": "Compact response (default true)",
                        },
                        "fields": {"type": "array", "items": _STR},
                    },
                    "required": ["title"],
                },
            ),
            ToolDefinition(
                name="tasks_update", title="Update task", idempotent=True,
                description=(
                    "Patch fields on a task (assignees accept usernames / me). "
                    "Supports type, parent_key, project_id, description_format."
                ),
                input_schema={
                    **_OBJ,
                    "properties": {
                        "key": _STR,
                        "title": _STR,
                        "description": _STR,
                        "description_format": {"type": "string", "enum": _DESC_FORMATS},
                        "type": {"type": "string", "enum": _TASK_TYPES},
                        "status": _STR,
                        "priority": {"type": "string", "enum": _PRIORITIES},
                        "assignees": {"type": "array", "items": _STR},
                        "due_at": _STR,
                        "project_id": _STR,
                        "parent_key": _STR,
                        "label_names": {"type": "array", "items": _STR},
                        "clear_assignee": _BOOL,
                        "compact": {"type": "boolean", "default": True},
                        "fields": {"type": "array", "items": _STR},
                    },
                    "required": ["key"],
                },
            ),
            ToolDefinition(
                name="tasks_transition", title="Transition status", idempotent=True,
                description="Change task status (validated by workflow on the API).",
                input_schema={
                    **_OBJ,
                    "properties": {
                        "key": _STR,
                        "status": _STR,
                        "compact": {"type": "boolean", "default": True},
                        "fields": {"type": "array", "items": _STR},
                    },
                    "required": ["key", "status"],
                },
            ),
            ToolDefinition(
                name="tasks_bulk_upsert", title="Bulk upsert tasks", idempotent=True,
                description=(
                    "Bulk create/upsert items (max 100). Rows with ``external_id`` upsert "
                    "so retries are idempotent. Or pass ``external_id`` + fields for a "
                    "single PUT-by-external upsert."
                ),
                input_schema={
                    **_OBJ,
                    "properties": {
                        "items": {
                            "type": "array",
                            "items": _BULK_ITEM_SCHEMA,
                            "maxItems": 100,
                            "description": "Batch for POST …/items/bulk (max 100)",
                        },
                        "external_id": _STR,
                        "title": _STR,
                        "type": {"type": "string", "enum": _TASK_TYPES},
                        "description": _STR,
                        "description_format": {"type": "string", "enum": _DESC_FORMATS},
                        "item_description": {
                            "type": "string",
                            "description": "Alias for description (single upsert)",
                        },
                        "status": _STR,
                        "assignees": {"type": "array", "items": _STR},
                        "priority": {"type": "string", "enum": _PRIORITIES},
                        "project_id": _STR,
                    },
                },
            ),
            ToolDefinition(
                name="tasks_bulk_delete", title="Bulk delete tasks",
                description="Delete many tasks by key (max 100). Requires confirm=true.",
                input_schema={
                    **_OBJ,
                    "properties": {
                        "keys": {
                            "type": "array",
                            "items": _STR,
                            "minItems": 1,
                            "maxItems": 100,
                        },
                        "confirm": {
                            "type": "boolean",
                            "description": "Must be true to delete",
                            "default": False,
                        },
                    },
                    "required": ["keys"],
                },
                destructive=True,
            ),
            ToolDefinition(
                name="tasks_comment", title="Add comment",
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
                name="tasks_label", title="Manage label", idempotent=True,
                description=(
                    "Add or remove a label on a task. Remove accepts ``label_id`` or ``name``."
                ),
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
                name="tasks_link", title="Link task",
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
                name="tasks_delete", title="Delete task",
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
            ToolDefinition(
                name="tasks_activity", title="Task activity",
                description=(
                    "Discussion + history for a task (comments, status changes, …). "
                    "Comment payloads may include ``attachments`` with ``so_uri`` — "
                    "use tasks_comment_file_url to download."
                ),
                input_schema={
                    **_OBJ,
                    "properties": {
                        "key": _STR,
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 200,
                            "description": "Return only the last N events (default all)",
                        },
                    },
                    "required": ["key"],
                },
                read_only=True,
            ),
            ToolDefinition(
                name="tasks_comment_file_url", title="Comment file URL",
                description=(
                    "Presigned download URL for a chat attachment. Pass ``so_uri`` from "
                    "tasks_activity comment attachments."
                ),
                input_schema={
                    **_OBJ,
                    "properties": {
                        "key": _STR,
                        "comment_id": _STR,
                        "so_uri": _STR,
                    },
                    "required": ["key", "comment_id", "so_uri"],
                },
                read_only=True,
            ),
            ToolDefinition(
                name="tasks_comment_update", title="Edit comment", idempotent=True,
                description="Update a comment body.",
                input_schema={
                    **_OBJ,
                    "properties": {"key": _STR, "comment_id": _STR, "body": _STR},
                    "required": ["key", "comment_id", "body"],
                },
            ),
            ToolDefinition(
                name="tasks_comment_delete", title="Delete comment",
                description="Delete a comment. Requires confirm=true.",
                input_schema={
                    **_OBJ,
                    "properties": {
                        "key": _STR,
                        "comment_id": _STR,
                        "confirm": {"type": "boolean", "default": False},
                    },
                    "required": ["key", "comment_id"],
                },
                destructive=True,
            ),
            ToolDefinition(
                name="tasks_archive", title="Archive task",
                description="Archive a task (optional cancel=true).",
                input_schema={
                    **_OBJ,
                    "properties": {
                        "key": _STR,
                        "cancel": _BOOL,
                        "compact": {"type": "boolean", "default": True},
                    },
                    "required": ["key"],
                },
            ),
            ToolDefinition(
                name="tasks_restore", title="Restore task",
                description="Restore an archived task.",
                input_schema={
                    **_OBJ,
                    "properties": {
                        "key": _STR,
                        "compact": {"type": "boolean", "default": True},
                    },
                    "required": ["key"],
                },
            ),
            ToolDefinition(
                name="tasks_watch", title="Watch task", idempotent=True,
                description="Add a watcher (default me).",
                input_schema={
                    **_OBJ,
                    "properties": {"key": _STR, "user": {**_STR, "default": "me"}},
                    "required": ["key"],
                },
            ),
            ToolDefinition(
                name="tasks_unwatch", title="Unwatch task", idempotent=True,
                description="Remove a watcher (default me).",
                input_schema={
                    **_OBJ,
                    "properties": {"key": _STR, "user": {**_STR, "default": "me"}},
                    "required": ["key"],
                },
            ),
            ToolDefinition(
                name="tasks_relations", title="List relations",
                description="List related-task links for a task.",
                input_schema={**_OBJ, "properties": {"key": _STR}, "required": ["key"]},
                read_only=True,
            ),
            ToolDefinition(
                name="tasks_unlink", title="Unlink relation/resource",
                description="Remove a relation (relation_id) or resource link (link_id).",
                input_schema={
                    **_OBJ,
                    "properties": {
                        "key": _STR,
                        "relation_id": _STR,
                        "link_id": {
                            **_STR,
                            "description": "Resource link id (from task.resources)",
                        },
                        "confirm": {"type": "boolean", "default": False},
                    },
                    "required": ["key"],
                },
                destructive=True,
            ),
            ToolDefinition(
                name="tasks_labels_list", title="List labels",
                description="Account-wide task labels.",
                input_schema={
                    **_OBJ,
                    "properties": {"include_archived": _BOOL},
                },
                read_only=True,
            ),
            ToolDefinition(
                name="tasks_share", title="Manage shares",
                description="Create, list, or revoke public share links for a task.",
                input_schema={
                    **_OBJ,
                    "properties": {
                        "key": _STR,
                        "action": {
                            "type": "string",
                            "enum": ["create", "list", "revoke"],
                            "default": "list",
                        },
                        "expires_in": {**_STR, "default": "never"},
                        "label": _STR,
                        "include_discussion": _BOOL,
                        "share_id": _STR,
                        "confirm": {
                            "type": "boolean",
                            "description": "Required true for revoke",
                            "default": False,
                        },
                    },
                    "required": ["key"],
                },
            ),
            ToolDefinition(
                name="tasks_projects", title="List/create projects",
                description=(
                    "List Tasks board projects, or create one (name required; slug optional)."
                ),
                input_schema={
                    **_OBJ,
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["list", "create"],
                            "default": "list",
                        },
                        "name": _STR,
                        "slug": _STR,
                        "description": _STR,
                    },
                },
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
            "tasks_bulk_delete": self._bulk_delete,
            "tasks_comment": self._comment,
            "tasks_label": self._label,
            "tasks_link": self._link,
            "tasks_delete": self._delete,
            "tasks_activity": self._activity,
            "tasks_comment_file_url": self._comment_file_url,
            "tasks_comment_update": self._comment_update,
            "tasks_comment_delete": self._comment_delete,
            "tasks_archive": self._archive,
            "tasks_restore": self._restore,
            "tasks_watch": self._watch,
            "tasks_unwatch": self._unwatch,
            "tasks_relations": self._relations,
            "tasks_unlink": self._unlink,
            "tasks_labels_list": self._labels_list,
            "tasks_share": self._share,
            "tasks_projects": self._projects,
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
        raw_items = page.get("items", [])
        cards = [task_card_markdown(i) for i in raw_items[:8]]
        items = raw_items
        if compact and fields is None:
            items = [compact_task_summary(i) for i in raw_items]
        else:
            items = apply_fields(raw_items, fields)
        out: dict[str, Any] = {
            "items": items,
            "total": page.get("total"),
            "next_cursor": page.get("next_cursor"),
        }
        if cards:
            out["__markdown__"] = "\n\n---\n\n".join(cards)
        return out

    def _get(self, args: dict[str, Any]) -> Any:
        key = args["key"]
        mark_seen = bool(args.get("mark_seen", False))
        item = self._tasks.get(key, mark_seen=mark_seen)
        card = task_card_markdown(item)
        if args.get("fields") is not None:
            body = apply_fields(item, args.get("fields"))
        elif args.get("compact"):
            body = compact_task_summary(item)
        else:
            body = item
        if isinstance(body, dict):
            return {**body, "__markdown__": card}
        return {"item": body, "__markdown__": card}

    def _schema(self, _args: dict[str, Any]) -> Any:
        return self._tasks.schema()

    def _people_list(self, _args: dict[str, Any]) -> Any:
        return {"items": self._tasks.people()}

    def _create(self, args: dict[str, Any]) -> Any:
        payload = {
            k: v
            for k, v in args.items()
            if k not in ("fields", "compact") and v is not None
        }
        title = payload.pop("title")
        item = self._tasks.create(title, **payload)
        return _compact_write(item, args)

    def _update(self, args: dict[str, Any]) -> Any:
        key = args["key"]
        fields = {
            k: v
            for k, v in args.items()
            if k not in ("key", "fields", "compact") and v is not None
        }
        item = self._tasks.update(key, **fields)
        return _compact_write(item, args)

    def _transition(self, args: dict[str, Any]) -> Any:
        item = self._tasks.update(args["key"], status=args["status"])
        return _compact_write(item, args)

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

    def _bulk_delete(self, args: dict[str, Any]) -> Any:
        if not args.get("confirm"):
            raise HomeCloudError("tasks_bulk_delete requires confirm=true")
        keys = args.get("keys") or []
        if not keys:
            raise HomeCloudError("tasks_bulk_delete requires keys")
        return self._tasks.bulk_delete(list(keys))

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
            name = args.get("name")
            if not name:
                raise HomeCloudError("tasks_label remove requires label_id or name")
            label_id = self._resolve_label_id(name)
        return self._tasks.remove_label(key, label_id)

    def _resolve_label_id(self, name: str) -> str:
        want = name.strip().lower()
        for row in self._tasks.labels():
            if str(row.get("name", "")).strip().lower() == want:
                lid = row.get("id")
                if lid:
                    return str(lid)
        raise HomeCloudError(f"label not found: {name}")

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

    def _activity(self, args: dict[str, Any]) -> Any:
        items = self._tasks.activity(args["key"])
        limit = args.get("limit")
        if isinstance(limit, int) and limit > 0:
            items = items[-limit:]
        return {"items": items, "total": len(items)}

    def _comment_file_url(self, args: dict[str, Any]) -> Any:
        return self._tasks.comment_file_url(
            args["key"], args["comment_id"], so_uri=args["so_uri"]
        )

    def _comment_update(self, args: dict[str, Any]) -> Any:
        return self._tasks.comment_update(args["key"], args["comment_id"], args["body"])

    def _comment_delete(self, args: dict[str, Any]) -> Any:
        if not args.get("confirm"):
            raise HomeCloudError("tasks_comment_delete requires confirm=true")
        return self._tasks.comment_delete(args["key"], args["comment_id"])

    def _archive(self, args: dict[str, Any]) -> Any:
        item = self._tasks.archive(args["key"], cancel=bool(args.get("cancel", False)))
        return _compact_write(item, args)

    def _restore(self, args: dict[str, Any]) -> Any:
        item = self._tasks.restore(args["key"])
        return _compact_write(item, args)

    def _watch(self, args: dict[str, Any]) -> Any:
        return self._tasks.watch(args["key"], args.get("user") or "me")

    def _unwatch(self, args: dict[str, Any]) -> Any:
        return self._tasks.unwatch(args["key"], args.get("user") or "me")

    def _relations(self, args: dict[str, Any]) -> Any:
        return {"items": self._tasks.list_relations(args["key"])}

    def _unlink(self, args: dict[str, Any]) -> Any:
        if not args.get("confirm"):
            raise HomeCloudError("tasks_unlink requires confirm=true")
        key = args["key"]
        if args.get("relation_id"):
            self._tasks.unlink_relation(key, args["relation_id"])
            return {"unlinked": "relation", "id": args["relation_id"]}
        if args.get("link_id"):
            return self._tasks.unlink_resource(key, args["link_id"])
        raise HomeCloudError("tasks_unlink requires relation_id or link_id")

    def _labels_list(self, args: dict[str, Any]) -> Any:
        return {
            "items": self._tasks.labels(
                include_archived=bool(args.get("include_archived", False))
            )
        }

    def _share(self, args: dict[str, Any]) -> Any:
        key = args["key"]
        action = args.get("action") or "list"
        if action == "list":
            return {"items": self._tasks.list_shares(key)}
        if action == "create":
            return self._tasks.create_share(
                key,
                expires_in=args.get("expires_in") or "never",
                label=args.get("label"),
                include_discussion=bool(args.get("include_discussion", False)),
            )
        if action == "revoke":
            if not args.get("confirm"):
                raise HomeCloudError("tasks_share revoke requires confirm=true")
            share_id = args.get("share_id")
            if not share_id:
                raise HomeCloudError("tasks_share revoke requires share_id")
            self._tasks.revoke_share(key, share_id)
            return {"revoked": share_id}
        raise HomeCloudError(f"unknown tasks_share action: {action}")

    def _projects(self, args: dict[str, Any]) -> Any:
        action = args.get("action") or "list"
        if action == "list":
            return {"items": self._tasks.list_projects()}
        if action == "create":
            name = args.get("name")
            if not name:
                raise HomeCloudError("tasks_projects create requires name")
            return self._tasks.create_project(
                name, slug=args.get("slug"), description=args.get("description")
            )
        raise HomeCloudError(f"unknown tasks_projects action: {action}")

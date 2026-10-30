# homecloud-mcp

Platform-wide [Model Context Protocol](https://modelcontextprotocol.io/) server for HomeCloud. Auth and HTTP go through **homecloud-sdk** (`HomeCloudClient` — profile, JWT session, or Access Key). The core registry is service-agnostic; **Tasks** is the first module (`tasks_*` tools). SO, MQ, Compute, and others can be added as new modules under `homecloud_mcp/modules/`.

## Install

From this monorepo (editable SDK + MCP):

```bash
cd homecloud-mcp
pip install -e ../homecloud-sdk -e ".[dev]"
```

Configure credentials the same way as the CLI (`homecloud configure`, `homecloud login`, or `HC_*` env vars). Tasks tools need a **user-bound** Access Key or a console JWT.

## Run

stdio transport (for Cursor and other MCP hosts):

```bash
homecloud-mcp
# or
python -m homecloud_mcp
```

Optional: `HC_PROFILE=prod homecloud-mcp`

## Cursor MCP config

Add to `.cursor/mcp.json` (adjust Python path if needed):

```json
{
  "mcpServers": {
    "homecloud": {
      "command": "homecloud-mcp",
      "env": {
        "HC_PROFILE": "default"
      }
    }
  }
}
```

If the script is not on `PATH`, use the venv interpreter:

```json
{
  "mcpServers": {
    "homecloud": {
      "command": "C:\\path\\to\\venv\\Scripts\\python.exe",
      "args": ["-m", "homecloud_mcp"],
      "env": {
        "HC_PROFILE": "default"
      }
    }
  }
}
```

## Tasks tools

| Tool | Notes |
|------|--------|
| `tasks_search` | List/search; default compact rows |
| `tasks_get` | Default `mark_seen=false` (no side effects) |
| `tasks_schema` | Types, statuses, transitions |
| `tasks_people_list` | Account users for `@` references |
| `tasks_create` / `tasks_update` / `tasks_transition` | Mutations |
| `tasks_bulk_upsert` | `items` batch or `external_id` upsert |
| `tasks_comment` / `tasks_label` / `tasks_link` | Discussion, labels, relations/resources |
| `tasks_delete` | Requires `confirm=true` |

## Adding a service module

1. Copy `homecloud_mcp/modules/_example_stub.py` to a new module file.
2. Implement `ServiceModule`: `name`, `list_tools()`, `call_tool()`.
3. Prefix tool names with the service id (`compute_list`, …).
4. Register in `homecloud_mcp/modules/__init__.py` → `default_modules()`.

The core package (`homecloud_mcp/core/`) must not import service modules directly; only `modules/__init__.py` wires them in.

## Tests

```bash
pytest
```

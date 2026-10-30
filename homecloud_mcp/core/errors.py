"""Shape SDK and unexpected errors for MCP tool responses."""

from __future__ import annotations

from typing import Any

from homecloud_core.errors import HomeCloudError


def tool_error_payload(exc: BaseException) -> dict[str, Any]:
    if isinstance(exc, HomeCloudError):
        return {"error": str(exc), "code": "homecloud_error"}
    return {"error": str(exc), "code": "internal_error"}

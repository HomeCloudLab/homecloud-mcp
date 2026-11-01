"""Shape SDK and unexpected errors for MCP tool responses."""

from __future__ import annotations

from typing import Any

from homecloud_core.errors import HomeCloudError


def tool_error_payload(exc: BaseException) -> dict[str, Any]:
    if isinstance(exc, HomeCloudError):
        payload: dict[str, Any] = {
            "error": str(exc),
            "code": getattr(exc, "code", None) or "homecloud_error",
        }
        details = getattr(exc, "details", None)
        if isinstance(details, dict) and details:
            payload["details"] = details
        status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
        if status is not None:
            payload["status"] = status
        return payload
    return {"error": str(exc), "code": "internal_error"}

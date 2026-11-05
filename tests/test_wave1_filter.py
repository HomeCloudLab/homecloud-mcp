"""Wave 1 remote tool allowlist — shared core filter."""

from __future__ import annotations

from unittest.mock import MagicMock

from homecloud_mcp.modules import REMOTE_WAVE1_TOOLS, build_registry


def test_remote_wave1_tools_only_tasks_search():
    assert REMOTE_WAVE1_TOOLS == frozenset({"tasks_search"})


def test_build_registry_filter_exposes_only_allowlist():
    client = MagicMock()
    reg = build_registry(client, include_tools=REMOTE_WAVE1_TOOLS)
    names = [t.name for t in reg.list_tools()]
    assert names == ["tasks_search"]


def test_build_registry_default_includes_more_than_wave1():
    client = MagicMock()
    reg = build_registry(client)
    names = {t.name for t in reg.list_tools()}
    assert "tasks_search" in names
    assert "tasks_get" in names
    assert len(names) > 1

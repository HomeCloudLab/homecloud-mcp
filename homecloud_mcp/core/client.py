"""HomeCloudClient factory — profile, JWT session, or Access Key."""

from __future__ import annotations

import os

from homecloud_sdk import HomeCloudClient


def build_client() -> HomeCloudClient:
    """
    Build SDK client from environment and credentials file.

    Honors ``HC_PROFILE`` / ``HOMECLOUD_PROFILE``, Access Key env vars, and
    console session from ``homecloud login``.
    """
    profile = os.environ.get("HC_PROFILE") or os.environ.get("HOMECLOUD_PROFILE")
    return HomeCloudClient.from_env(profile=profile)


def client_from_bearer(
    token: str,
    *,
    account_id: str | None = None,
    console_base_url: str | None = None,
    apex: str | None = None,
) -> HomeCloudClient:
    """Ephemeral client that uses a Console JWT (does not write ``~/.homecloud/session``).

    Used by Remote MCP / tests. Access Key env vars are ignored once the bearer is set.
    """
    client = HomeCloudClient(
        account_id=account_id,
        apex=apex,
        console_base_url=console_base_url,
        interactive_mfa=False,
    )
    # Bypass session file: stamp transport only.
    client._ctx._transport.access_token = token
    if account_id:
        client._ctx._account_id = account_id
    return client

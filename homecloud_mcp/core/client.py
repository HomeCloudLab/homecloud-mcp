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

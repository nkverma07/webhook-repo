"""
Application configuration.

All secrets/credentials must come from environment variables.
"""

from __future__ import annotations

import os


class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-key")  # override in prod

    # MongoDB
    # Example: mongodb://localhost:27017/webhook_repo
    MONGO_URI = os.getenv("MONGO_URI", "")

    # Operational defaults
    JSON_SORT_KEYS = False


def validate_config(cfg: type[Config]) -> None:
    """
    Validate required configuration at startup.
    """
    if not cfg.MONGO_URI:
        raise RuntimeError(
            "Missing required env var MONGO_URI. "
            "Example: set MONGO_URI=mongodb://localhost:27017/webhook_repo"
        )

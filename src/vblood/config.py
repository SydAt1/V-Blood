"""
Application configuration for V-Blood.

Reads from environment variables, with defaults appropriate for
local development. Production deployments must set these explicitly.
All secrets (database passwords, API keys) must be provided via
environment variables, never hard-coded.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file if present (development only; not for production)
load_dotenv()


class AppConfig:
    """Central application configuration resolved from environment variables."""

    # --- Environment ---
    env: str = os.getenv("VBLOOD_ENV", "development")
    log_level: str = os.getenv("VBLOOD_LOG_LEVEL", "INFO").upper()
    version: str = os.getenv("VBLOOD_VERSION", "0.1.0")

    # --- API ---
    api_host: str = os.getenv("VBLOOD_API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("VBLOOD_API_PORT", "8000"))

    # --- Artifact storage ---
    artifact_dir: Path = Path(os.getenv("VBLOOD_ARTIFACT_DIR", "./simulation_outputs"))

    # --- Database (not required for Milestone 1 standalone engine) ---
    db_host: str | None = os.getenv("VBLOOD_DB_HOST")
    db_port: int | None = int(os.getenv("VBLOOD_DB_PORT", "5432")) if os.getenv("VBLOOD_DB_PORT") else None
    db_name: str | None = os.getenv("VBLOOD_DB_NAME")
    db_user: str | None = os.getenv("VBLOOD_DB_USER")
    # Never log the password value
    _db_password: str | None = os.getenv("VBLOOD_DB_PASSWORD")

    @classmethod
    def is_development(cls) -> bool:
        """Return True when running in development mode."""
        return cls.env == "development"

    @classmethod
    def db_available(cls) -> bool:
        """Return True when all required database configuration is present."""
        return all([cls.db_host, cls.db_name, cls.db_user, cls._db_password])


# Module-level singleton
config = AppConfig()

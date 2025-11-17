"""
Centralized configuration for ETL pipeline.

Provides a single source of truth for all ETL configuration,
replacing scattered environment variables and flags.
"""

import os
from dataclasses import dataclass
from typing import Literal, Optional
from enum import Enum
from errors import EtlError


class SecretsMode(Enum):
    """How to access secrets."""
    ENV = "env"  # Read from environment variables
    GCP = "gcp"  # Read from Google Cloud Secret Manager


class EnvProfile(Enum):
    """Environment profile for the ETL run.
    Values loaded from common/config.json python_env_profiles.
    """
    DEV = "dev"
    STAGING = "staging"
    E2E = "e2e"
    DEMO = "demo"
    PROD = "prod"
    
    @classmethod
    def get_safe_profiles(cls) -> List["EnvProfile"]:
        """Get list of safe (non-production) profiles from config."""
        from config_loader import get_safe_profiles
        safe_names = get_safe_profiles()
        return [cls(name) for name in safe_names if name in [e.value for e in cls]]


@dataclass
class SecretsConfig:
    """Configuration for secret access."""
    mode: SecretsMode
    project_id: str

    @classmethod
    def from_env(cls) -> "SecretsConfig":
        """Create SecretsConfig from environment variables."""
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
        if not project_id:
            raise EtlError("No GCP project configured. Set GOOGLE_CLOUD_PROJECT or GCP_PROJECT environment variable.")

        # Determine secrets mode
        if os.environ.get("DISABLE_SECRET_MANAGER") or os.environ.get("E2E_LIVE_DB") == "1":
            mode = SecretsMode.ENV
        else:
            mode = SecretsMode.GCP

        return cls(mode=mode, project_id=project_id)


@dataclass
class EtlConfig:
    """Complete configuration for ETL pipeline."""

    # Environment and safety
    env_profile: EnvProfile
    project_id: str
    collection_name: str

    # Secrets configuration
    secrets: SecretsConfig

    # ETL behavior
    memos_mode: Literal["none", "api"]
    max_concurrent_scrapes: int
    dry_run: bool
    animal_limit: Optional[int]
    skip_events_people: bool  # Skip events and people fetching for testing

    @classmethod
    def from_env(cls, overrides: Optional[dict] = None) -> "EtlConfig":
        """Create EtlConfig from environment variables with optional overrides."""
        overrides = overrides or {}

        # Environment profile
        env_profile_str = overrides.get("env_profile") or os.environ.get("ENV_PROFILE", "dev")
        try:
            env_profile = EnvProfile(env_profile_str.lower())
        except ValueError:
            raise EtlError(f"Invalid ENV_PROFILE: {env_profile_str}. Must be one of: {[e.value for e in EnvProfile]}")

        # Project and collection
        project_id = overrides.get("project_id") or (os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT"))
        if not project_id:
            raise EtlError("No GCP project configured. Set GOOGLE_CLOUD_PROJECT or GCP_PROJECT environment variable.")

        collection_name = overrides.get("collection_name") or os.environ.get("DOGS_COLLECTION", "dogs")

        # Secrets config
        secrets = SecretsConfig.from_env()

        # ETL behavior defaults
        memos_mode = overrides.get("memos_mode") or os.environ.get("MEMOS_MODE", "api")
        if memos_mode not in ["none", "api"]:
            raise EtlError(f"Invalid MEMOS_MODE: {memos_mode}. Must be 'none' or 'api'")

        max_concurrent_scrapes = overrides.get("max_concurrent_scrapes") or int(os.environ.get("MAX_CONCURRENT_SCRAPES", "2"))
        dry_run = overrides.get("dry_run", False)
        animal_limit = overrides.get("animal_limit")
        skip_events_people = overrides.get("skip_events_people", os.environ.get("SKIP_EVENTS_PEOPLE", "").lower() in ("true", "1", "yes"))

        return cls(
            env_profile=env_profile,
            project_id=project_id,
            collection_name=collection_name,
            secrets=secrets,
            memos_mode=memos_mode,  # type: ignore
            max_concurrent_scrapes=max_concurrent_scrapes,
            dry_run=dry_run,
            animal_limit=animal_limit,
            skip_events_people=skip_events_people,
        )

    def is_prod(self) -> bool:
        """Check if this is a production environment."""
        return self.env_profile == EnvProfile.PROD

    def is_dev_safe(self) -> bool:
        """Check if this configuration is safe for development operations."""
        safe_profiles = {EnvProfile.DEV, EnvProfile.STAGING, EnvProfile.E2E, EnvProfile.DEMO}
        return self.env_profile in safe_profiles


def assert_dev_safe_config(config: EtlConfig, operation: str) -> None:
    """Assert that the configuration is safe for development operations."""
    if not config.is_dev_safe():
        raise EtlError(f"Refusing to run {operation} against {config.env_profile.value} environment. "
                      f"Allowed profiles: {[p.value for p in EnvProfile if p != EnvProfile.PROD]}")


def load_dotenv_files() -> None:
    """
    Load dotenv files for local development.
    Call this function explicitly to load .env and .env.local files.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv('.env')
        load_dotenv('.env.local')
    except ImportError:
        # dotenv not available, continue with existing env vars
        pass

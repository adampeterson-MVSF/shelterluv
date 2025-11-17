"""
Centralized configuration for ETL pipeline.

Provides a single source of truth for all ETL configuration,
replacing scattered environment variables and flags.
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import List, Literal, Optional

from errors import EtlError


class SecretsMode(Enum):
    """How to access secrets."""

    ENV = "env"  # Read from environment variables
    GCP = "gcp"  # Read from Google Cloud Secret Manager


class EnvProfile(Enum):
    """Environment profile for the ETL run.
    Values loaded from common/config.json python_env_profiles.
    """

    # Static members for known profiles - these will be validated against config
    DEV = "dev"
    STAGING = "staging"
    E2E = "e2e"
    DEMO = "demo"
    MAIN = "main"

    def is_safe(self) -> bool:
        """
        Check if this profile is safe for development operations.
        Uses normalized profile map as single source of truth.
        """
        try:
            from .config_loader import get_normalized_profile_map
        except ImportError:
            from config_loader import get_normalized_profile_map
        profile_map = get_normalized_profile_map()
        return profile_map.get(self.value, {}).get("is_safe", False)

    def project_id(self) -> str:
        """
        Get the GCP project ID for this environment profile.
        Uses python_env_profiles from config as single source of truth.
        """
        try:
            from .config_loader import get_python_env_profiles
        except ImportError:
            from config_loader import get_python_env_profiles
        python_profiles = get_python_env_profiles()
        if self.value not in python_profiles:
            raise ValueError(f"No GCP project mapping found for profile '{self.value}'")
        return python_profiles[self.value]["gcp_project"]

    @classmethod
    def get_safe_profiles(cls) -> List["EnvProfile"]:
        """
        Get list of safe (non-production) profile enum values.
        Uses normalized profile map as single source of truth.
        """
        try:
            from .config_loader import get_normalized_profile_map
        except ImportError:
            from config_loader import get_normalized_profile_map
        profile_map = get_normalized_profile_map()
        return [cls(profile) for profile, info in profile_map.items() if info.get("is_safe", False)]


@dataclass
class SecretsConfig:
    """Configuration for secret access."""

    mode: SecretsMode
    project_id: str

    @classmethod
    def from_env(cls, project_id: str) -> "SecretsConfig":
        """
        Create SecretsConfig from environment variables.

        Args:
            project_id: GCP project ID (required).

        Returns:
            SecretsConfig instance
        """
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
        try:
            from .config_loader import get_python_env_profiles
        except ImportError:
            from config_loader import get_python_env_profiles

        overrides = overrides or {}

        # Environment profile
        env_profile_str = overrides.get("env_profile") or os.environ.get("ENV_PROFILE", "dev")
        try:
            env_profile = EnvProfile(env_profile_str.lower())
        except ValueError:
            raise EtlError(
                f"Invalid ENV_PROFILE: {env_profile_str}. Must be one of: {[e.value for e in EnvProfile]}"
            )

        # Resolve project_id from profile
        project_id = overrides.get("project_id") or env_profile.project_id()

        # Validate project_id override against safety map
        if overrides.get("project_id"):
            try:
                from .config_loader import get_project_safety
            except ImportError:
                from config_loader import get_project_safety
            safety_map = get_project_safety()
            if project_id not in safety_map:
                raise EtlError(
                    f"Invalid project_id override '{project_id}': not found in configured projects. "
                    f"Valid projects: {sorted(safety_map.keys())}"
                )

        collection_name = overrides.get("collection_name") or os.environ.get(
            "DOGS_COLLECTION", "dogs"
        )

        # Secrets config - use the resolved project_id
        secrets = SecretsConfig.from_env(project_id=project_id)

        # ETL behavior defaults
        memos_mode = overrides.get("memos_mode") or os.environ.get("MEMOS_MODE", "api")
        if memos_mode not in ["none", "api"]:
            raise EtlError(f"Invalid MEMOS_MODE: {memos_mode}. Must be 'none' or 'api'")

        max_concurrent_scrapes = overrides.get("max_concurrent_scrapes") or int(
            os.environ.get("MAX_CONCURRENT_SCRAPES", "10")
        )
        dry_run = overrides.get("dry_run", False)
        animal_limit = overrides.get("animal_limit")
        skip_events_people = overrides.get(
            "skip_events_people",
            os.environ.get("SKIP_EVENTS_PEOPLE", "true").lower() in ("true", "1", "yes"),
        )

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
        return self.env_profile.is_safe()


@dataclass
class SafetyPolicy:
    """Unified safety policy for ETL operations.

    Mirrors the logic from JS devScriptSafety.js for consistency across languages.
    Safety is defined over project IDs, not profile names.
    """

    env_profile: EnvProfile
    project_id: str
    dev_scripts_enabled: bool
    dry_run: bool

    def is_safe_project(self) -> bool:
        """
        Check if the current project is safe for development operations.
        Uses project-based safety mapping as single source of truth.
        Mirrors JS devScriptSafety.isSafeProject() logic.
        A project is safe if ANY profile that maps to it is safe.
        """
        try:
            from .config_loader import get_project_safety
        except ImportError:
            from config_loader import get_project_safety
        safety = get_project_safety()
        info = safety.get(self.project_id)
        return bool(info and info["is_safe"])

    def is_safe_for_operation(self, operation: str, destructive: bool = True) -> bool:
        """
        Check if an operation is safe given this policy.
        Mirrors JS devScriptSafety.assertSafe() logic.

        Args:
            operation: Description of the operation (for error messages)
            destructive: Whether this is a destructive operation

        Returns:
            True if operation is safe, False otherwise
        """
        # Dry run is always safe
        if self.dry_run:
            return True

        # Non-destructive operations just need safe project
        if not destructive:
            return self.is_safe_project()

        # Destructive operations require both dev scripts enabled AND safe project
        return self.dev_scripts_enabled and self.is_safe_project()

    def assert_safe_for_operation(self, operation: str, destructive: bool = True) -> None:
        """
        Assert that an operation is safe, raising EtlError if not.
        Mirrors JS devScriptSafety.assertSafe() logic.

        Args:
            operation: Description of the operation (for error messages)
            destructive: Whether this is a destructive operation

        Raises:
            EtlError: If operation is not safe
        """
        if not self.is_safe_for_operation(operation, destructive):
            if destructive and not self.dev_scripts_enabled:
                raise EtlError(f"Refusing to run {operation}: DEV_SCRIPTS_ENABLED=1 required")
            if not self.is_safe_project():
                safe_profile_names = [p.value for p in EnvProfile.get_safe_profiles()]
                raise EtlError(
                    f"Refusing to run {operation} against {self.env_profile.value} environment. "
                    f"Allowed profiles: {safe_profile_names}"
                )

    @classmethod
    def from_config_and_env(cls, config: EtlConfig) -> "SafetyPolicy":
        """Create SafetyPolicy from EtlConfig and environment."""
        dev_scripts_enabled = os.environ.get("DEV_SCRIPTS_ENABLED") == "1"
        return cls(
            env_profile=config.env_profile,
            project_id=config.project_id,
            dev_scripts_enabled=dev_scripts_enabled,
            dry_run=config.dry_run,
        )


def assert_dev_safe_config(config: EtlConfig, operation: str) -> None:
    """Assert that the configuration is safe for development operations."""
    policy = SafetyPolicy.from_config_and_env(config)
    policy.assert_safe_for_operation(operation)


def load_dotenv_files() -> None:
    """
    Load dotenv files for local development.
    Call this function explicitly to load .env and .env.local files.
    """
    try:
        from dotenv import load_dotenv

        load_dotenv(".env")
        load_dotenv(".env.local")
    except ImportError:
        # dotenv not available, continue with existing env vars
        pass

"""
Load configuration from common/config.json.
Provides Python access to unified configuration metadata.
Validates consistency with EnvProfile enum.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List


def _load_config() -> Dict[str, Any]:
    """Load config.json from common directory."""
    # Find common/config.json relative to this file
    # This file is in services/etl_scraper_py/, so go up two levels
    repo_root = Path(__file__).parent.parent.parent
    config_path = repo_root / "common" / "config.json"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


_CONFIG = _load_config()

# Cache for validation result to avoid repeated checks
_config_validated = False


def _validate_config_consistency() -> None:
    """
    Validate that config.json python_env_profiles keys match EnvProfile enum.
    Called lazily on first access to fail fast if there's a mismatch.
    """
    global _config_validated
    if _config_validated:
        return

    try:
        from .config import EnvProfile
    except ImportError:
        # Skip validation if running as script (not as package)
        # This allows the module to be imported for testing/config access
        # without requiring the full package structure
        return

    config_profiles = set(_CONFIG["python_env_profiles"].keys())
    enum_profiles = {e.value for e in EnvProfile}

    # Check for profiles in config that aren't in enum
    extra_in_config = config_profiles - enum_profiles
    if extra_in_config:
        raise ValueError(
            f"config.json python_env_profiles contains profiles not in EnvProfile enum: {extra_in_config}. "
            f"Valid enum values: {sorted(enum_profiles)}"
        )

    # Check for profiles in enum that aren't in config
    missing_in_config = enum_profiles - config_profiles
    if missing_in_config:
        raise ValueError(
            f"EnvProfile enum contains profiles not in config.json python_env_profiles: {missing_in_config}. "
            f"Config profiles: {sorted(config_profiles)}"
        )

    _config_validated = True


def get_python_env_profiles() -> Dict[str, Dict[str, str]]:
    """Get Python-specific environment profiles (GCP project mappings)."""
    _validate_config_consistency()
    return _CONFIG["python_env_profiles"]


def get_env_profiles() -> Dict[str, Dict[str, List[str]]]:
    """Get environment variable profiles from config."""
    return _CONFIG["env_profiles"]


def get_safe_profiles() -> List[str]:
    """Get list of safe (non-production) profile names."""
    return _CONFIG["safe_profiles"]


def get_roles() -> List[str]:
    """Get list of valid user roles."""
    return _CONFIG["roles"]


def get_normalized_profile_map() -> Dict[str, Dict[str, Any]]:
    """
    Get normalized profile map for safety checks.
    Single source of truth for profile -> {gcp_project, is_safe} mappings.
    Mirrors JS getNormalizedProfileMap() for cross-language consistency.
    """
    _validate_config_consistency()
    profile_map = {}

    python_profiles = _CONFIG["python_env_profiles"]
    safe_profiles = set(_CONFIG["safe_profiles"])

    for profile_name, profile_config in python_profiles.items():
        profile_map[profile_name] = {
            "gcp_project": profile_config["gcp_project"],
            "is_safe": profile_name in safe_profiles
        }

    return profile_map


def get_project_safety() -> Dict[str, Dict[str, Any]]:
    """
    Get project-based safety mapping.
    Single source of truth for project_id -> {is_safe} mappings.
    Mirrors JS devScriptSafety.isSafeProject() logic for cross-language consistency.
    A project is safe if ANY profile that maps to it is safe.
    """
    _validate_config_consistency()
    safety_map = {}

    python_profiles = _CONFIG["python_env_profiles"]
    safe_profiles = set(_CONFIG["safe_profiles"])

    for profile_name, profile_config in python_profiles.items():
        project_id = profile_config["gcp_project"]
        is_safe = profile_name in safe_profiles

        if project_id not in safety_map:
            safety_map[project_id] = {"is_safe": is_safe}
        else:
            # If any profile mapping to this project is safe, the project is safe
            safety_map[project_id]["is_safe"] = safety_map[project_id]["is_safe"] or is_safe

    return safety_map

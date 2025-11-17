"""
Load configuration from generated config artifact.
Provides Python access to unified configuration metadata.
Delegates to generated artifact for validated, normalized data.
"""

from typing import Any, Dict, List

try:
    # Try relative import (when used as package)
    from .config_artifact import CONFIG_ARTIFACT, get_env_profiles, get_safe_profiles, get_roles, get_profile_safety_map, get_project_safety_map, is_profile_safe, is_project_safe
except ImportError:
    # Fall back to absolute import (when run as script)
    from config_artifact import CONFIG_ARTIFACT, get_env_profiles, get_safe_profiles, get_roles, get_profile_safety_map, get_project_safety_map, is_profile_safe, is_project_safe

# For backward compatibility, expose the raw artifact as _CONFIG
_CONFIG = CONFIG_ARTIFACT

# Cache for validation result to avoid repeated checks
_config_validated = False


def _validate_config_consistency() -> None:
    """
    Validate that generated artifact profile keys match EnvProfile enum.
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

    artifact_profiles = set(CONFIG_ARTIFACT["profile_safety_map"].keys())
    enum_profiles = {e.value for e in EnvProfile}

    # Check for profiles in artifact that aren't in enum
    extra_in_artifact = artifact_profiles - enum_profiles
    if extra_in_artifact:
        raise ValueError(
            f"Generated config artifact contains profiles not in EnvProfile enum: {extra_in_artifact}. "
            f"Valid enum values: {sorted(enum_profiles)}. "
            f"Run 'npm run schema:gen' to regenerate artifacts."
        )

    # Check for profiles in enum that aren't in artifact
    missing_in_artifact = enum_profiles - artifact_profiles
    if missing_in_artifact:
        raise ValueError(
            f"EnvProfile enum contains profiles not in generated config artifact: {missing_in_artifact}. "
            f"Artifact profiles: {sorted(artifact_profiles)}. "
            f"Run 'npm run schema:gen' to regenerate artifacts."
        )

    _config_validated = True


def get_python_env_profiles() -> Dict[str, Dict[str, str]]:
    """Get Python-specific environment profiles (GCP project mappings)."""
    _validate_config_consistency()
    # Canonical way to get env profile -> GCP project mappings from artifact
    result = {}
    for profile_name, profile_data in CONFIG_ARTIFACT["profile_safety_map"].items():
        result[profile_name] = {"gcp_project": profile_data["gcp_project"]}
    return result


def get_env_profiles() -> Dict[str, Dict[str, List[str]]]:
    """Get environment variable profiles from config."""
    return CONFIG_ARTIFACT["env_profiles"]


def get_safe_profiles() -> List[str]:
    """Get list of safe (non-production) profile names."""
    return CONFIG_ARTIFACT["safe_profiles"]


def get_roles() -> List[str]:
    """Get list of valid user roles."""
    return CONFIG_ARTIFACT["roles"]


def get_normalized_profile_map() -> Dict[str, Dict[str, Any]]:
    """
    Get normalized profile map for safety checks.
    Single source of truth for profile -> {gcp_project, is_safe} mappings.
    Mirrors JS getNormalizedProfileMap() for cross-language consistency.
    """
    _validate_config_consistency()
    return get_profile_safety_map()


def get_project_safety() -> Dict[str, Dict[str, Any]]:
    """
    Get project-based safety mapping.
    Single source of truth for project_id -> {is_safe} mappings.
    Mirrors JS devScriptSafety.isSafeProject() logic for cross-language consistency.
    A project is safe if ANY profile that maps to it is safe.
    """
    _validate_config_consistency()
    return get_project_safety_map()

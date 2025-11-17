"""
Project safety utilities for ETL scripts.
Provides checks to ensure operations are only run against safe (development) projects.
"""

import os


def ensure_dev_project() -> None:
    """Ensure we are running in a development/test environment, not production.

    Uses unified config.json to determine safe projects instead of hardcoded checks.
    """
    from config_loader import get_python_env_profiles, get_safe_profiles

    project_id = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise ValueError("Must set GCP_PROJECT or GOOGLE_CLOUD_PROJECT")

    # Check if project is in safe profiles list from unified config
    python_profiles = get_python_env_profiles()
    safe_profiles = get_safe_profiles()

    is_safe = False
    for profile_name in safe_profiles:
        profile = python_profiles.get(profile_name)
        if profile and profile.get("gcp_project") == project_id:
            is_safe = True
            break

    if not is_safe:
        safe_projects = [
            str(gcp_project)
            for p in safe_profiles
            if (gcp_project := python_profiles.get(p, {}).get("gcp_project")) is not None
        ]
        raise ValueError(
            f"Refusing to run against project '{project_id}'. "
            f"Safe projects: {', '.join(safe_projects)}"
        )


# Backward compatibility alias
guard_dev_only = ensure_dev_project

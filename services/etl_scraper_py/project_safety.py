"""
Project safety utilities for ETL scripts.
Provides checks to ensure operations are only run against safe (development) projects.
"""

import os
from config import SafetyPolicy, EtlConfig


def ensure_dev_project() -> None:
    """Ensure we are running in a development/test environment, not production.

    Uses SafetyPolicy as the single source of truth for safety checks.
    """
    # Create minimal config for safety checking
    config = EtlConfig.from_env()
    policy = SafetyPolicy.from_config_and_env(config)
    policy.assert_safe_for_operation("development operation")


# Backward compatibility alias
guard_dev_only = ensure_dev_project

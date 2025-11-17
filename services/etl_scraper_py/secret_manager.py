"""
Secret management for ETL pipeline.

Provides a clean API for accessing secrets from either Google Cloud Secret Manager
or environment variables, based on configuration.
"""

import os
from functools import lru_cache
from typing import Any, Dict

from config import SecretsConfig, SecretsMode
from errors import EtlError


@lru_cache
def _get_gcp_secret_client():
    """Get cached Google Cloud Secret Manager client."""
    from google.cloud import secretmanager

    return secretmanager.SecretManagerServiceClient()


def _get_secret_from_gcp(project_id: str, secret_name: str, version: str = "latest") -> str:
    """Fetch a secret from Google Cloud Secret Manager."""
    client = _get_gcp_secret_client()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/{version}"

    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def _get_secret_from_env(secret_name: str) -> str:
    """Fetch a secret from environment variables."""
    value = os.environ.get(secret_name)
    if value is None or value.strip() == "":
        raise EtlError(f"Secret {secret_name} not found in environment variables")
    return value.strip('"')


def get_secret(secrets_config: SecretsConfig, secret_name: str, version: str = "latest") -> str:
    """
    Fetch a secret using the configured method.

    Args:
        secrets_config: Configuration for how to access secrets
        secret_name: Name of the secret to fetch
        version: Version of the secret (default: "latest")

    Returns:
        The secret value as a string

    Raises:
        EtlError: If the secret cannot be retrieved
    """
    if secrets_config.mode == SecretsMode.GCP:
        return _get_secret_from_gcp(secrets_config.project_id, secret_name, version)
    elif secrets_config.mode == SecretsMode.ENV:
        return _get_secret_from_env(secret_name)
    else:
        raise EtlError(f"Unsupported secrets mode: {secrets_config.mode}")


def get_shelterluv_creds(secrets_config: SecretsConfig) -> Dict[str, str]:
    """
    Fetch all ShelterLuv credentials.

    Args:
        secrets_config: Configuration for how to access secrets

    Returns:
        Dict containing username, password, and api_key

    Raises:
        EtlError: If any credentials are missing
    """
    try:
        username = get_secret(secrets_config, "SHELTERLUV_USER")
        password = get_secret(secrets_config, "SHELTERLUV_PASS")
        api_key = get_secret(secrets_config, "SHELTERLUV_API_KEY")

        return {"username": username, "password": password, "api_key": api_key}
    except EtlError as e:
        raise EtlError(f"ShelterLuv credentials not found: {e}") from e

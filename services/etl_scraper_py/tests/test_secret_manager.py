"""
Tests for secret_manager.py - Google Secret Manager integration.
"""

import os
from unittest.mock import Mock, patch

import pytest

from errors import EtlError
from secret_manager import _get_gcp_secret_client, get_secret, get_shelterluv_creds


class TestSecretManager:
    """Test secret manager functionality."""

    @patch("google.cloud.secretmanager.SecretManagerServiceClient")
    def test_get_secret_client_caching(self, mock_client_class):
        """Test that _get_gcp_secret_client is properly cached."""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        # Clear cache before test
        _get_gcp_secret_client.cache_clear()

        # First call
        client1 = _get_gcp_secret_client()
        # Second call - should return cached instance
        client2 = _get_gcp_secret_client()

        # Should be the same instance (cached)
        assert client1 is client2
        # Should only create client once
        mock_client_class.assert_called_once()

    def test_get_secret_client_caching_attribute(self):
        """Test that _get_gcp_secret_client function has caching."""
        # Test that the function has the cache attribute (from @lru_cache)
        assert hasattr(_get_gcp_secret_client, "cache_clear")
        assert callable(_get_gcp_secret_client.cache_clear)

    @patch("secret_manager.get_secret")
    def test_get_shelterluv_creds_from_secret_manager(self, mock_get_secret):
        """Test successful credential retrieval from Secret Manager."""
        from config import SecretsConfig, SecretsMode

        mock_get_secret.side_effect = ["testuser", "testpass", "testkey"]

        secrets_config = SecretsConfig(mode=SecretsMode.GCP, project_id="test-project")
        result = get_shelterluv_creds(secrets_config)

        assert result == {"username": "testuser", "password": "testpass", "api_key": "testkey"}

        # Should call get_secret for each credential
        assert mock_get_secret.call_count == 3
        mock_get_secret.assert_any_call(secrets_config, "SHELTERLUV_USER")
        mock_get_secret.assert_any_call(secrets_config, "SHELTERLUV_PASS")
        mock_get_secret.assert_any_call(secrets_config, "SHELTERLUV_API_KEY")

    def test_get_shelterluv_creds_from_env_vars_only(self):
        """Test credential retrieval from environment variables."""
        from config import SecretsConfig, SecretsMode

        # Set environment variables
        env_vars = {
            "SHELTERLUV_USER": "env_user",
            "SHELTERLUV_PASS": "env_pass",
            "SHELTERLUV_API_KEY": "env_key",
        }

        with patch.dict(os.environ, env_vars):
            secrets_config = SecretsConfig(mode=SecretsMode.ENV, project_id="test-project")
            result = get_shelterluv_creds(secrets_config)

            # Should fall back to environment variables
            assert result == {"username": "env_user", "password": "env_pass", "api_key": "env_key"}

    def test_get_shelterluv_creds_from_env_vars_only(self):
        """Test credential retrieval from environment variables only."""
        from config import SecretsConfig, SecretsMode

        env_vars = {
            "SHELTERLUV_USER": "env_user",
            "SHELTERLUV_PASS": "env_pass",
            "SHELTERLUV_API_KEY": "env_key",
        }

        with patch.dict(os.environ, env_vars):
            secrets_config = SecretsConfig(mode=SecretsMode.ENV, project_id="test-project")
            result = get_shelterluv_creds(secrets_config)

            assert result == {"username": "env_user", "password": "env_pass", "api_key": "env_key"}

    def test_get_shelterluv_creds_missing_env_vars(self):
        """Test failure when credentials are missing from environment variables."""
        from config import SecretsConfig, SecretsMode

        secrets_config = SecretsConfig(mode=SecretsMode.ENV, project_id="test-project")

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EtlError, match="Secret SHELTERLUV_USER not found"):
                get_shelterluv_creds(secrets_config)

    def test_get_shelterluv_creds_partial_env_vars(self):
        """Test failure when some environment variables are missing."""
        from config import SecretsConfig, SecretsMode

        env_vars = {
            "SHELTERLUV_USER": "env_user",
            "SHELTERLUV_PASS": "env_pass",
            "SHELTERLUV_API_KEY": "",  # Explicitly empty
        }

        secrets_config = SecretsConfig(mode=SecretsMode.ENV, project_id="test-project")

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(EtlError, match="Secret SHELTERLUV_API_KEY not found"):
                get_shelterluv_creds(secrets_config)

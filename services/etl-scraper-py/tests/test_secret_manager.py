"""
Tests for secret_manager.py - Google Secret Manager integration.
"""

import pytest
import os
from unittest.mock import patch, Mock
from secret_manager import get_shelterluv_creds, get_secret, _get_gcp_secret_client
from errors import EtlError


class TestSecretManager:
    """Test secret manager functionality."""

    def test_get_secret_client_caching(self):
        """Test that _get_gcp_secret_client is properly cached."""
        with patch('secret_manager._ensure_google_cloud_imported') as mock_ensure_import:
            # Mock the secretmanager module after import
            from unittest.mock import MagicMock
            mock_secretmanager = MagicMock()
            mock_client_instance = MagicMock()

            with patch('secret_manager.secretmanager', mock_secretmanager):
                mock_secretmanager.SecretManagerServiceClient.return_value = mock_client_instance

                # First call
                client1 = _get_gcp_secret_client()
                # Second call - should return cached instance
                client2 = _get_gcp_secret_client()

                # Should be the same instance (cached)
                assert client1 is client2
                # Should only create client once
                mock_secretmanager.SecretManagerServiceClient.assert_called_once()

    def test_get_secret_caching(self):
        """Test that _get_secret function is properly cached."""
        # Test that the function has the cache attribute (from @lru_cache)
        assert hasattr(_get_secret, 'cache_clear')
        assert callable(_get_secret.cache_clear)

    @patch('secret_manager._get_secret')
    def test_get_shelterluv_creds_from_secret_manager(self, mock_get_secret):
        """Test successful credential retrieval from Secret Manager."""
        mock_get_secret.side_effect = ["testuser", "testpass", "testkey"]

        result = get_shelterluv_creds()

        assert result == {
            "username": "testuser",
            "password": "testpass",
            "api_key": "testkey"
        }

        # Should call _get_secret for each credential
        assert mock_get_secret.call_count == 3
        mock_get_secret.assert_any_call("SHELTERLUV_USER")
        mock_get_secret.assert_any_call("SHELTERLUV_PASS")
        mock_get_secret.assert_any_call("SHELTERLUV_API_KEY")

    @patch('secret_manager._get_secret')
    def test_get_shelterluv_creds_partial_secret_failure(self, mock_get_secret):
        """Test fallback to env vars when Secret Manager partially fails."""
        # Secret Manager fails completely (all secrets fail)
        mock_get_secret.side_effect = Exception("Secret Manager unavailable")

        # Set environment variables as fallback
        env_vars = {
            "SHELTERLUV_USER": "env_user",
            "SHELTERLUV_PASS": "env_pass",
            "SHELTERLUV_API_KEY": "env_key"
        }

        # Clear cache to ensure fresh call
        get_shelterluv_creds.cache_clear()
        with patch.dict(os.environ, env_vars):
            result = get_shelterluv_creds()

            # Should fall back to environment variables
            assert result == {
                "username": "env_user",
                "password": "env_pass",
                "api_key": "env_key"
            }

    def test_get_shelterluv_creds_from_env_vars_only(self):
        """Test credential retrieval from environment variables only."""
        env_vars = {
            "SHELTERLUV_USER": "env_user",
            "SHELTERLUV_PASS": "env_pass",
            "SHELTERLUV_API_KEY": "env_key"
        }

        # Clear cache to ensure fresh call
        get_shelterluv_creds.cache_clear()
        with patch.dict(os.environ, env_vars), \
             patch('secret_manager._get_secret', side_effect=Exception("No secrets")):
            result = get_shelterluv_creds()

            assert result == {
                "username": "env_user",
                "password": "env_pass",
                "api_key": "env_key"
            }

    def test_get_shelterluv_creds_missing_env_vars(self):
        """Test failure when credentials are missing from both sources."""
        # Clear cache to ensure fresh call
        get_shelterluv_creds.cache_clear()
        with patch.dict(os.environ, {}, clear=True), \
             patch('secret_manager._get_secret', side_effect=Exception("No secrets")):
            with pytest.raises(EtlError, match="ShelterLuv credentials not found"):
                get_shelterluv_creds()

    def test_get_shelterluv_creds_partial_env_vars(self):
        """Test failure when some environment variables are missing."""
        env_vars = {
            "SHELTERLUV_USER": "env_user",
            "SHELTERLUV_PASS": "env_pass",
            "SHELTERLUV_API_KEY": ""  # Explicitly empty
        }

        # Clear cache to ensure fresh call
        get_shelterluv_creds.cache_clear()
        with patch.dict(os.environ, env_vars, clear=True), \
             patch('secret_manager._get_secret', side_effect=Exception("No secrets")):
            with pytest.raises(EtlError, match="ShelterLuv credentials not found"):
                get_shelterluv_creds()

    @patch('secret_manager._get_secret')
    def test_get_shelterluv_creds_caching(self, mock_get_secret):
        """Test that get_shelterluv_creds is properly cached."""
        mock_get_secret.side_effect = ["user", "pass", "key"]

        # Clear cache to ensure fresh call
        get_shelterluv_creds.cache_clear()

        # First call
        result1 = get_shelterluv_creds()
        # Second call - should use cached result
        result2 = get_shelterluv_creds()

        # Should be the same result
        assert result1 is result2
        # Should only call _get_secret 3 times for first call, then cached
        assert mock_get_secret.call_count == 3

    def test_project_id_configuration(self):
        """Test that PROJECT_ID is properly configured."""
        from secret_manager import PROJECT_ID
        # Test that PROJECT_ID is set to the expected default
        assert PROJECT_ID == "muttville"

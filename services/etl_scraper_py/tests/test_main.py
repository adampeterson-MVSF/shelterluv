"""
Tests for main.py - Cloud Function entry point.
"""

import os
from unittest.mock import Mock, patch

import pytest

from config import EnvProfile, EtlConfig, SecretsConfig, SecretsMode
from errors import EtlError
from main import check_auth, run_shelterluv_etl


@pytest.fixture(autouse=True)
def mock_gcp_project(monkeypatch):
    """Mocks the required GCP_PROJECT env var for main.py."""
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")


class TestMain:
    """Test the Cloud Function entry point."""

    def test_check_auth_success_with_header_token(self):
        """Test authentication succeeds with valid header token."""
        request = Mock()
        request.headers = {"X-ShelterLuv-Token": "valid-token"}
        request.args = {}

        with patch.dict(os.environ, {"SHELTERLUV_ETL_TOKEN": "valid-token"}):
            assert check_auth(request) is True

    def test_check_auth_success_with_query_param(self):
        """Test authentication succeeds with valid query parameter."""
        request = Mock()
        request.headers = {}
        request.args = {"token": "valid-token"}

        with patch.dict(os.environ, {"SHELTERLUV_ETL_TOKEN": "valid-token"}):
            assert check_auth(request) is True

    def test_check_auth_header_takes_precedence(self):
        """Test that header token takes precedence over query param."""
        request = Mock()
        request.headers = {"X-ShelterLuv-Token": "valid-token"}
        request.args = {"token": "different-token"}

        with patch.dict(os.environ, {"SHELTERLUV_ETL_TOKEN": "valid-token"}):
            assert check_auth(request) is True

    def test_check_auth_failure_wrong_token(self):
        """Test authentication fails with wrong token."""
        request = Mock()
        request.headers = {"X-ShelterLuv-Token": "wrong-token"}
        request.args = {}

        with patch.dict(os.environ, {"SHELTERLUV_ETL_TOKEN": "valid-token"}):
            assert check_auth(request) is False

    def test_check_auth_failure_no_token(self):
        """Test authentication fails with no token provided."""
        request = Mock()
        request.headers = {}
        request.args = {}

        with patch.dict(os.environ, {"SHELTERLUV_ETL_TOKEN": "valid-token"}):
            assert check_auth(request) is False

    def test_check_auth_failure_no_env_var(self):
        """Test authentication fails when environment variable is not set."""
        request = Mock()
        request.headers = {"X-ShelterLuv-Token": "some-token"}
        request.args = {}

        with patch.dict(os.environ, {}, clear=True):
            assert check_auth(request) is False

    @patch("main.get_shelterluv_creds")
    @patch("main.pipeline.run_etl_process")
    @patch("main.EtlConfig.from_env")
    def test_run_shelterluv_etl_success(self, mock_config_from_env, mock_etl_run, mock_get_creds):
        """Test successful ETL run."""
        # Create a mock config
        mock_config = Mock(spec=EtlConfig)
        mock_config.secrets = Mock(spec=SecretsConfig)
        mock_config_from_env.return_value = mock_config

        mock_etl_run.return_value = {
            "num_animals_fetched_from_api": 5,
            "dogs_processed": 5,
            "dogs_written": 5,
        }
        mock_get_creds.return_value = {
            "api_key": "test_key",
            "username": "test",
            "password": "test",
        }

        request = Mock()
        request.headers = {"X-ShelterLuv-Token": "valid-token"}
        request.args = {}

        with patch.dict(
            os.environ,
            {"SHELTERLUV_ETL_TOKEN": "valid-token", "GOOGLE_CLOUD_PROJECT": "test-project"},
        ):
            response, status_code = run_shelterluv_etl(request)

            assert status_code == 200
            assert response["status"] == "ok"
            assert "run_id" in response
            assert response["stats"]["num_animals_fetched_from_api"] == 5
            mock_etl_run.assert_called_once()
            mock_get_creds.assert_called_once()
            mock_config_from_env.assert_called_once_with(overrides={"env_profile": "prod"})

    def test_run_shelterluv_etl_unauthorized(self):
        """Test ETL run fails with unauthorized access."""
        request = Mock()
        request.headers = {"X-ShelterLuv-Token": "wrong-token"}
        request.args = {}

        with patch.dict(os.environ, {"SHELTERLUV_ETL_TOKEN": "valid-token"}):
            response, status_code = run_shelterluv_etl(request)

            assert status_code == 401
            assert response["status"] == "error"
            assert response["message"] == "Unauthorized"

    @patch("main.get_shelterluv_creds")
    @patch("main.pipeline.run_etl_process")
    @patch("main.EtlConfig.from_env")
    def test_run_shelterluv_etl_etl_error(self, mock_config_from_env, mock_etl_run, mock_get_creds):
        """Test ETL run handles EtlError properly."""
        # Create a mock config
        mock_config = Mock(spec=EtlConfig)
        mock_config.secrets = Mock(spec=SecretsConfig)
        mock_config_from_env.return_value = mock_config

        mock_etl_run.side_effect = EtlError("Test error")
        mock_get_creds.return_value = {"username": "test", "password": "test", "api_key": "test"}

        request = Mock()
        request.headers = {"X-ShelterLuv-Token": "valid-token"}
        request.args = {}

        with patch.dict(
            os.environ,
            {"SHELTERLUV_ETL_TOKEN": "valid-token", "GOOGLE_CLOUD_PROJECT": "test-project"},
        ):
            response, status_code = run_shelterluv_etl(request)

            assert status_code == 500
            assert response["status"] == "error"
            assert "run_id" in response
            assert response["message"] == "ETL Error: Test error"

    @patch("main.get_shelterluv_creds")
    @patch("main.pipeline.run_etl_process")
    @patch("main.EtlConfig.from_env")
    def test_run_shelterluv_etl_unexpected_error(
        self, mock_config_from_env, mock_etl_run, mock_get_creds
    ):
        """Test ETL run handles unexpected exceptions properly."""
        # Create a mock config
        mock_config = Mock(spec=EtlConfig)
        mock_config.secrets = Mock(spec=SecretsConfig)
        mock_config_from_env.return_value = mock_config

        mock_etl_run.side_effect = Exception("Unexpected error")
        mock_get_creds.return_value = {"username": "test", "password": "test", "api_key": "test"}

        request = Mock()
        request.headers = {"X-ShelterLuv-Token": "valid-token"}
        request.args = {}

        with patch.dict(
            os.environ,
            {"SHELTERLUV_ETL_TOKEN": "valid-token", "GOOGLE_CLOUD_PROJECT": "test-project"},
        ):
            response, status_code = run_shelterluv_etl(request)

            assert status_code == 500
            assert response["status"] == "error"
            assert "run_id" in response
            assert "Internal server error" in response["message"]

    @patch("main.get_shelterluv_creds")
    @patch("main.pipeline.run_etl_process")
    @patch("main.EtlConfig.from_env")
    def test_run_shelterluv_etl_with_dry_run(
        self, mock_config_from_env, mock_etl_run, mock_get_creds
    ):
        """Test that ETL run supports dry_run parameter from config."""
        # Create a mock config
        mock_config = Mock(spec=EtlConfig)
        mock_config.secrets = Mock(spec=SecretsConfig)
        mock_config_from_env.return_value = mock_config

        mock_etl_run.return_value = {"status": "success"}
        mock_get_creds.return_value = {"username": "test", "password": "test", "api_key": "test"}

        request = Mock()
        request.headers = {"X-ShelterLuv-Token": "valid-token"}
        request.args = {}

        with patch.dict(
            os.environ,
            {"SHELTERLUV_ETL_TOKEN": "valid-token", "GOOGLE_CLOUD_PROJECT": "test-project"},
        ):
            run_shelterluv_etl(request)

            # Should call etl.run_etl_process with config and creds
            mock_etl_run.assert_called_once()

    def test_run_shelterluv_etl_run_id_format(self):
        """Test that run_id follows expected format."""
        request = Mock()
        request.headers = {"X-ShelterLuv-Token": "valid-token"}
        request.args = {}

        # Create a mock config
        mock_config = Mock(spec=EtlConfig)
        mock_config.secrets = Mock(spec=SecretsConfig)

        with patch.dict(
            os.environ,
            {"SHELTERLUV_ETL_TOKEN": "valid-token", "GOOGLE_CLOUD_PROJECT": "test-project"},
        ), patch("main.EtlConfig.from_env", return_value=mock_config), patch(
            "main.get_shelterluv_creds",
            return_value={"username": "test", "password": "test", "api_key": "test"},
        ), patch(
            "main.pipeline.run_etl_process", return_value={}
        ) as mock_etl:
            response, _ = run_shelterluv_etl(request)

            run_id = response["run_id"]
            # Should be ISO format with Z suffix
            assert run_id.endswith("Z")
            assert "T" in run_id  # ISO format has T separator
            mock_etl.assert_called_once()

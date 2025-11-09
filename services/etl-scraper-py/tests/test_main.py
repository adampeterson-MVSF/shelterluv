"""
Tests for main.py - Cloud Function entry point.
"""

import pytest
import os
from unittest.mock import patch, Mock
from main import check_auth, run_shelterluv_etl
from errors import EtlError


@pytest.fixture(autouse=True)
def mock_gcp_project(monkeypatch):
    """Mocks the required GCP_PROJECT env var for main.py."""
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")


class TestMain:
    """Test the Cloud Function entry point."""

    def test_check_auth_success_with_header_token(self):
        """Test authentication succeeds with valid header token."""
        request = Mock()
        request.headers = {'X-ShelterLuv-Token': 'valid-token'}
        request.args = {}

        with patch.dict(os.environ, {'SHELTERLUV_ETL_TOKEN': 'valid-token'}):
            assert check_auth(request) is True

    def test_check_auth_success_with_query_param(self):
        """Test authentication succeeds with valid query parameter."""
        request = Mock()
        request.headers = {}
        request.args = {'token': 'valid-token'}

        with patch.dict(os.environ, {'SHELTERLUV_ETL_TOKEN': 'valid-token'}):
            assert check_auth(request) is True

    def test_check_auth_header_takes_precedence(self):
        """Test that header token takes precedence over query param."""
        request = Mock()
        request.headers = {'X-ShelterLuv-Token': 'valid-token'}
        request.args = {'token': 'different-token'}

        with patch.dict(os.environ, {'SHELTERLUV_ETL_TOKEN': 'valid-token'}):
            assert check_auth(request) is True

    def test_check_auth_failure_wrong_token(self):
        """Test authentication fails with wrong token."""
        request = Mock()
        request.headers = {'X-ShelterLuv-Token': 'wrong-token'}
        request.args = {}

        with patch.dict(os.environ, {'SHELTERLUV_ETL_TOKEN': 'valid-token'}):
            assert check_auth(request) is False

    def test_check_auth_failure_no_token(self):
        """Test authentication fails with no token provided."""
        request = Mock()
        request.headers = {}
        request.args = {}

        with patch.dict(os.environ, {'SHELTERLUV_ETL_TOKEN': 'valid-token'}):
            assert check_auth(request) is False

    def test_check_auth_failure_no_env_var(self):
        """Test authentication fails when environment variable is not set."""
        request = Mock()
        request.headers = {'X-ShelterLuv-Token': 'some-token'}
        request.args = {}

        with patch.dict(os.environ, {}, clear=True):
            assert check_auth(request) is False

    @patch('pipeline.run_etl_process')
    def test_run_shelterluv_etl_success(self, mock_etl_run):
        """Test successful ETL run."""
        mock_etl_run.return_value = {
            "total_animals_fetched": 5,
            "dogs_processed": 5,
            "dogs_written": 5
        }

        request = Mock()
        request.headers = {'X-ShelterLuv-Token': 'valid-token'}
        request.args = {}

        with patch.dict(os.environ, {'SHELTERLUV_ETL_TOKEN': 'valid-token'}):
            response, status_code = run_shelterluv_etl(request)

            assert status_code == 200
            assert response["status"] == "ok"
            assert "run_id" in response
            assert response["stats"]["total_animals_fetched"] == 5
            mock_etl_run.assert_called_once_with()

    def test_run_shelterluv_etl_unauthorized(self):
        """Test ETL run fails with unauthorized access."""
        request = Mock()
        request.headers = {'X-ShelterLuv-Token': 'wrong-token'}
        request.args = {}

        with patch.dict(os.environ, {'SHELTERLUV_ETL_TOKEN': 'valid-token'}):
            response, status_code = run_shelterluv_etl(request)

            assert status_code == 401
            assert response["status"] == "error"
            assert response["message"] == "Unauthorized"

    @patch('pipeline.run_etl_process')
    def test_run_shelterluv_etl_etl_error(self, mock_etl_run):
        """Test ETL run handles EtlError properly."""
        mock_etl_run.side_effect = EtlError("ETL processing failed")

        request = Mock()
        request.headers = {'X-ShelterLuv-Token': 'valid-token'}
        request.args = {}

        with patch.dict(os.environ, {'SHELTERLUV_ETL_TOKEN': 'valid-token'}):
            response, status_code = run_shelterluv_etl(request)

            assert status_code == 500
            assert response["status"] == "error"
            assert "run_id" in response
            assert response["message"] == "ETL processing failed"

    @patch('pipeline.run_etl_process')
    def test_run_shelterluv_etl_unexpected_error(self, mock_etl_run):
        """Test ETL run handles unexpected exceptions properly."""
        mock_etl_run.side_effect = Exception("Unexpected error")

        request = Mock()
        request.headers = {'X-ShelterLuv-Token': 'valid-token'}
        request.args = {}

        with patch.dict(os.environ, {'SHELTERLUV_ETL_TOKEN': 'valid-token'}):
            response, status_code = run_shelterluv_etl(request)

            assert status_code == 500
            assert response["status"] == "error"
            assert "run_id" in response
            assert response["message"] == "Internal server error"

    @patch('pipeline.run_etl_process')
    def test_run_shelterluv_etl_with_dry_run(self, mock_etl_run):
        """Test that ETL run doesn't support dry_run parameter from HTTP request."""
        mock_etl_run.return_value = {"status": "success"}

        request = Mock()
        request.headers = {'X-ShelterLuv-Token': 'valid-token'}
        request.args = {}

        with patch.dict(os.environ, {'SHELTERLUV_ETL_TOKEN': 'valid-token'}):
            run_shelterluv_etl(request)

            # Should call etl.run_etl_process with default dry_run=False
            mock_etl_run.assert_called_once_with()

    def test_run_shelterluv_etl_run_id_format(self):
        """Test that run_id follows expected format."""
        request = Mock()
        request.headers = {'X-ShelterLuv-Token': 'valid-token'}
        request.args = {}

        with patch.dict(os.environ, {'SHELTERLUV_ETL_TOKEN': 'valid-token'}), \
             patch('pipeline.run_etl_process', return_value={}) as mock_etl:
            response, _ = run_shelterluv_etl(request)

            run_id = response["run_id"]
            # Should be ISO format with Z suffix
            assert run_id.endswith('Z')
            assert 'T' in run_id  # ISO format has T separator
            mock_etl.assert_called_once_with()

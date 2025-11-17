"""
Tests for schema validation and field normalization.
Tests status normalization, age normalization, and schema validation.

CREDENTIALS: These tests use mocked services where possible.
Real ShelterLuv credentials come from:
- .env.local file in services/etl_scraper_py/ (for local development)
- Google Cloud Secret Manager (for production)

Required environment variables (in .env.local):
- SHELTERLUV_USER=your_username
- SHELTERLUV_PASS=your_password
- SHELTERLUV_API_KEY=your_api_key

If tests fail due to missing credentials:
1. Create services/etl_scraper_py/.env.local
2. Add the required SHELTERLUV_* variables
3. Run: python check_credentials.py to verify
"""

from unittest import mock

import pytest

from main import check_auth
from schema import (
    _build_age_display,
    _normalize_age_years,
    _normalize_status,
    get_required_fields,
    validate_dog_record,
)


class TestStatusNormalization:
    """Test status field normalization."""

    def test_normalize_status_available(self):
        assert _normalize_status("Available") == "AVAILABLE"
        assert _normalize_status("available") == "AVAILABLE"

    def test_normalize_status_pending(self):
        assert _normalize_status("Pending") == "PENDING"
        assert _normalize_status("pending") == "PENDING"

    def test_normalize_status_adopted(self):
        assert _normalize_status("Adopted") == "ADOPTED"
        assert _normalize_status("adopted") == "ADOPTED"
        assert _normalize_status("Serviced Out") == "ADOPTED"
        assert _normalize_status("Healthy in Home") == "ADOPTED"

    def test_normalize_status_hold(self):
        assert _normalize_status("Hold") == "HOLD"
        assert _normalize_status("hold") == "HOLD"

    def test_normalize_status_unknown(self):
        assert _normalize_status("Unknown") == "UNKNOWN"
        assert _normalize_status("") == "UNKNOWN"
        assert _normalize_status(None) == "UNKNOWN"
        assert _normalize_status("invalid_status") == "UNKNOWN"


class TestAgeNormalization:
    """Test age parsing and normalization."""

    def test_normalize_age_years_years_only(self):
        assert _normalize_age_years("3 years") == 3.0
        assert _normalize_age_years("1 year") == 1.0

    def test_normalize_age_years_months_only(self):
        assert _normalize_age_years("6 months") == 0.5
        # Rounded to 0.1 precision
        assert _normalize_age_years("1 month") == pytest.approx(0.1, abs=0.01)

    def test_normalize_age_years_years_and_months(self):
        # Rounded to 0.1 precision: 2 years 3 months = 2.25 → 2.2
        assert _normalize_age_years("2 years 3 months") == pytest.approx(2.2, abs=0.01)
        assert _normalize_age_years("1 year 6 months") == 1.5

    def test_normalize_age_years_invalid(self):
        assert _normalize_age_years("") == 0.0
        assert _normalize_age_years(None) == 0.0
        assert _normalize_age_years("unknown") == 0.0

    def test_normalize_age_years_pure_number_as_months(self):
        """Test that pure numeric strings (no units) are treated as months."""
        # This tests normalization.py's behavior, not schema.py's
        from normalization import _normalize_age_years as norm_normalize_age_years

        # 101 months = 8.4 years (Oso's case)
        assert norm_normalize_age_years("101") == pytest.approx(8.4, abs=0.1)
        # 24 months = 2 years
        assert norm_normalize_age_years("24") == 2.0
        # 6 months = 0.5 years
        assert norm_normalize_age_years("6") == 0.5

    def test_build_age_display_years(self):
        assert _build_age_display(3.0) == "3 years"
        assert _build_age_display(1.0) == "1 year"

    def test_build_age_display_months(self):
        assert _build_age_display(0.5) == "6 months"
        # 0.083 rounds to 0 months in display logic
        assert _build_age_display(0.1) == "1 month"

    def test_build_age_display_years_and_months(self):
        assert _build_age_display(2.25) == "2 years 3 months"
        assert _build_age_display(1.5) == "1 year 6 months"

    def test_build_age_display_unknown(self):
        assert _build_age_display(0.0) == "Unknown"


class TestSchemaValidation:
    """Test JSON schema validation."""

    def test_get_required_fields_matches_schema(self):
        """Test that get_required_fields() returns the expected required fields."""
        required_fields = get_required_fields()
        expected_fields = [
            "Internal-ID",
            "ID",
            "Name",
            "Status",
            "AgeYears",
            "AgeDisplay",
            "IsInCustody",
            "IsAvailableForAdoption",
            "IsHospice",
            "IsEventDog",
            "PersonalityNotes",
            "IntakeNotes",
            "MedicalNotes",
        ]
        assert set(required_fields) == set(expected_fields)

    def test_valid_minimal_dog_record(self):
        """Test validation of a minimal valid dog record with all required fields."""
        dog = {
            "Internal-ID": "123",
            "ID": "A123",
            "Name": "Test Dog",
            "Status": "AVAILABLE",
            "AgeYears": 3.0,
            "AgeDisplay": "3 years",
            "IsInCustody": True,
            "IsAvailableForAdoption": True,
            "IsHospice": False,
            "IsEventDog": False,
            "PersonalityNotes": "",
            "IntakeNotes": "",
            "MedicalNotes": "",
        }
        # Should not raise
        validate_dog_record(dog)

    def test_invalid_missing_required_field(self):
        """Test validation fails when required field is missing."""
        dog = {
            "Internal-ID": "123",
            "ID": "A123",
            "Name": "Test Dog",
            "Status": "AVAILABLE",
            # Missing AgeYears and other required fields
        }
        with pytest.raises(Exception):  # SchemaValidationError
            validate_dog_record(dog)

    @pytest.mark.parametrize(
        "missing_field",
        [
            "Internal-ID",
            "ID",
            "Name",
            "Status",
            "AgeYears",
            "AgeDisplay",
            "IsInCustody",
            "IsAvailableForAdoption",
            "IsHospice",
            "IsEventDog",
        ],
    )
    def test_invalid_missing_each_required_field(self, missing_field):
        """Test validation fails when each individual required field is missing."""
        dog = {
            "Internal-ID": "123",
            "ID": "A123",
            "Name": "Test Dog",
            "Status": "AVAILABLE",
            "AgeYears": 3.0,
            "AgeDisplay": "3 years",
            "IsInCustody": True,
            "IsAvailableForAdoption": True,
            "IsHospice": False,
            "IsEventDog": False,
        }
        # Remove the field we're testing
        del dog[missing_field]

        with pytest.raises(Exception):  # SchemaValidationError
            validate_dog_record(dog)

    def test_invalid_wrong_enum_value(self):
        """Test validation fails with invalid enum value."""
        dog = {
            "Internal-ID": "123",
            "ID": "A123",
            "Name": "Test Dog",
            "Status": "INVALID_STATUS",  # Not in enum
            "AgeYears": 3.0,
            "AgeDisplay": "3 years",
            "IsInCustody": True,
            "IsAvailableForAdoption": True,
            "IsHospice": False,
            "IsEventDog": False,
        }
        with pytest.raises(Exception):  # SchemaValidationError
            validate_dog_record(dog)


class TestETLRequiredFieldsEmission:
    """Test that ETL pipeline always emits required fields."""

    def test_etl_emits_all_required_fields(self):
        """Test that ETL pipeline output includes all required fields."""
        from pipeline import ExtractResult
        from transform import TransformConfig, transform

        # Create a minimal extract result with one animal
        extract_result = ExtractResult(
            in_custody_ids={"123"},
            animals_by_id={
                "123": {
                    "Internal-ID": "123",
                    "ID": "A123",
                    "Name": "Test Dog",
                    "Status": "Available",
                    "Age": "3 years",
                }
            },
            events=[],
            people=[],
            existing_metadata={},
            memos_data={},
            scraped_map={},
        )

        # Mock credentials (we're not actually calling APIs)
        creds = {"username": "test", "password": "test", "api_key": "test"}

        # Run transform (this should add all required fields)
        config = TransformConfig()

        # Add scraped data and memos to extract result (now done in extract phase)
        extract_result.scraped_map = {"123": {}}
        extract_result.memos_data = {}

        result = transform(extract_result, creds, config)

        # Should have produced one dog
        assert len(result.dogs) == 1
        dog = result.dogs[0]

        # Check that all required fields are present
        required_fields = get_required_fields()
        for field in required_fields:
            assert field in dog, f"ETL output missing required field: {field}"
            assert dog[field] is not None, f"ETL output has null required field: {field}"

    def test_etl_output_passes_schema_validation(self):
        """Test that all ETL output passes schema validation."""
        from pipeline import ExtractResult
        from transform import TransformConfig, transform

        # Create extract result with a valid animal
        extract_result = ExtractResult(
            in_custody_ids={"123"},
            animals_by_id={
                "123": {
                    "Internal-ID": "123",
                    "ID": "A123",
                    "Name": "Test Dog",
                    "Status": "Available",
                    "Age": "3 years",
                }
            },
            events=[],
            people=[],
            existing_metadata={},
            memos_data={},
            scraped_map={},
        )

        creds = {"username": "test", "password": "test", "api_key": "test"}
        config = TransformConfig()

        # Add scraped data and memos to extract result (now done in extract phase)
        extract_result.scraped_map = {"123": {}}
        extract_result.memos_data = {}

        result = transform(extract_result, creds, config)

        # All produced dogs should pass schema validation
        for dog in result.dogs:
            validate_dog_record(dog)  # Should not raise


class TestAuthLogic:
    """Test authentication logic in main.py."""

    def test_check_auth_no_env_token(self, monkeypatch):
        """Test auth fails when no environment token is set."""
        monkeypatch.delenv("SHELTERLUV_ETL_TOKEN", raising=False)

        class MockRequest:
            def __init__(self):
                self.headers = {}
                self.args = {}

        request = MockRequest()
        assert check_auth(request) == False

    def test_check_auth_valid_header_token(self, monkeypatch):
        """Test auth succeeds with valid header token."""
        monkeypatch.setenv("SHELTERLUV_ETL_TOKEN", "test-token-123")

        class MockRequest:
            def __init__(self):
                self.headers = {"X-ShelterLuv-Token": "test-token-123"}
                self.args = {}

        request = MockRequest()
        assert check_auth(request) == True

    def test_check_auth_valid_query_token(self, monkeypatch):
        """Test auth succeeds with valid query parameter token."""
        monkeypatch.setenv("SHELTERLUV_ETL_TOKEN", "test-token-456")

        class MockRequest:
            def __init__(self):
                self.headers = {}
                self.args = {"token": "test-token-456"}

        request = MockRequest()
        assert check_auth(request) == True

    def test_check_auth_invalid_token(self, monkeypatch):
        """Test auth fails with invalid token."""
        monkeypatch.setenv("SHELTERLUV_ETL_TOKEN", "correct-token")

        class MockRequest:
            def __init__(self):
                self.headers = {"X-ShelterLuv-Token": "wrong-token"}
                self.args = {}

        request = MockRequest()
        assert check_auth(request) == False

    def test_check_auth_no_token_provided(self, monkeypatch):
        """Test auth fails when no token is provided in request."""
        monkeypatch.setenv("SHELTERLUV_ETL_TOKEN", "test-token")

        class MockRequest:
            def __init__(self):
                self.headers = {}
                self.args = {}

        request = MockRequest()
        assert check_auth(request) == False

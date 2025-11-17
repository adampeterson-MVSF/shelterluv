"""
Tests for schema validation to ensure Python types match dog.schema.json.
Tests that ETL pipeline produces data conforming to the JSON schema contract.
"""

import json
from typing import Any, Dict

import pytest

from errors import SchemaValidationError
from schema import (
    _build_age_display,
    _get_dog_schema,
    _normalize_age_years,
    _normalize_size,
    _normalize_status,
    get_normalized_sizes,
    get_normalized_statuses,
    get_required_fields,
    validate_dog_record,
)


class TestSchemaTypeValidation:
    """Test that Python types and values conform to JSON schema constraints."""

    @pytest.fixture
    def dog_schema(self):
        """Load the dog schema for testing."""
        return _get_dog_schema()

    def test_schema_loads_successfully(self, dog_schema):
        """Test that the schema file loads without errors."""
        assert isinstance(dog_schema, dict)
        assert dog_schema.get("type") == "object"
        assert "properties" in dog_schema
        assert "required" in dog_schema

    def test_required_fields_match_schema(self, dog_schema):
        """Test that get_required_fields() matches schema required array."""
        schema_required = set(dog_schema["required"])
        code_required = set(get_required_fields())

        # They should be identical
        assert (
            schema_required == code_required
        ), f"Required fields mismatch: schema={schema_required}, code={code_required}"

    def test_status_enum_matches_schema(self, dog_schema):
        """Test that Status enum values match between schema and code."""
        schema_statuses = set(dog_schema["properties"]["Status"]["enum"])
        code_statuses = set(get_normalized_statuses())

        assert (
            schema_statuses == code_statuses
        ), f"Status enum mismatch: schema={schema_statuses}, code={code_statuses}"

    def test_size_enum_matches_schema(self, dog_schema):
        """Test that Size enum values match between schema and code."""
        schema_sizes = set(dog_schema["properties"]["Size"]["enum"])
        code_sizes = set(get_normalized_sizes())

        assert (
            schema_sizes == code_sizes
        ), f"Size enum mismatch: schema={schema_sizes}, code={code_sizes}"

    def test_gender_enum_matches_schema(self, dog_schema):
        """Test that Gender enum values match schema."""
        schema_genders = set(dog_schema["properties"]["Gender"]["enum"])
        expected_genders = {"Male", "Female"}

        assert (
            schema_genders == expected_genders
        ), f"Gender enum mismatch: schema={schema_genders}, expected={expected_genders}"

    def test_boolean_fields_are_boolean_type(self, dog_schema):
        """Test that boolean fields are properly typed as boolean in schema."""
        boolean_fields = ["IsInCustody", "IsAvailableForAdoption", "IsHospice", "IsEventDog"]

        for field in boolean_fields:
            assert field in dog_schema["properties"], f"Missing boolean field: {field}"
            field_def = dog_schema["properties"][field]
            assert (
                field_def["type"] == "boolean"
            ), f"Field {field} should be boolean type, got {field_def['type']}"

    def test_string_fields_are_string_type(self, dog_schema):
        """Test that string fields are properly typed as string in schema."""
        string_fields = [
            "Internal-ID",
            "ID",
            "Name",
            "Breed",
            "AgeDisplay",
            "Size",
            "Gender",
            "Status",
            "Description",
            "CaseManager",
            "MemosRawHTML",
            "PersonalityNotes",
            "IntakeNotes",
            "MedicalNotes",
            "AdoptionCategory",
            "MedicalCategory",
            "BehaviorCategory",
            "FullAnimalProfile",
            "Location",
            "Stage",
            "FosterName",
            "FosterPhone",
            "FosterEmail",
            "ScrapeError",
        ]

        for field in string_fields:
            if field in dog_schema["properties"]:  # Some fields might not exist in all versions
                field_def = dog_schema["properties"][field]
                assert (
                    field_def["type"] == "string"
                ), f"Field {field} should be string type, got {field_def['type']}"

    def test_number_fields_are_number_type(self, dog_schema):
        """Test that number fields are properly typed as number in schema."""
        number_fields = ["AgeYears"]

        for field in number_fields:
            assert field in dog_schema["properties"], f"Missing number field: {field}"
            field_def = dog_schema["properties"][field]
            assert (
                field_def["type"] == "number"
            ), f"Field {field} should be number type, got {field_def['type']}"

    def test_array_fields_are_array_type(self, dog_schema):
        """Test that array fields are properly typed as array in schema."""
        array_fields = ["Photos", "Treatments"]

        for field in array_fields:
            if field in dog_schema["properties"]:  # Some fields might not exist in all versions
                field_def = dog_schema["properties"][field]
                assert (
                    field_def["type"] == "array"
                ), f"Field {field} should be array type, got {field_def['type']}"

    def test_photos_array_items_are_uri_strings(self, dog_schema):
        """Test that Photos array items are URI strings."""
        if "Photos" in dog_schema["properties"]:
            photos_def = dog_schema["properties"]["Photos"]
            assert "items" in photos_def
            items_def = photos_def["items"]
            assert items_def["type"] == "string"
            assert items_def.get("format") == "uri"

    def test_treatments_array_structure(self, dog_schema):
        """Test that Treatments array has proper object structure."""
        if "Treatments" in dog_schema["properties"]:
            treatments_def = dog_schema["properties"]["Treatments"]
            assert "items" in treatments_def
            items_def = treatments_def["items"]
            assert items_def["type"] == "object"
            assert "properties" in items_def

            # Check required treatment fields
            required_props = ["date", "treatment", "notes"]
            for prop in required_props:
                assert prop in items_def["properties"], f"Missing treatment property: {prop}"
                assert (
                    items_def["properties"][prop]["type"] == "string"
                ), f"Treatment {prop} should be string"


class TestNormalizationFunctions:
    """Test that normalization functions produce schema-compliant values."""

    def test_normalize_size_produces_valid_values(self):
        """Test that _normalize_size produces only valid Size enum values."""
        test_cases = [
            ("Small", "Small"),
            ("small", "Small"),
            ("MEDIUM", "Medium"),
            ("Large", "Large"),
            ("X-Large", "X-Large"),
            ("extra large", "X-Large"),
            ("", "UNKNOWN"),
            (None, "UNKNOWN"),
            ("invalid", "UNKNOWN"),
        ]

        valid_sizes = set(get_normalized_sizes())

        for input_val, expected in test_cases:
            result = _normalize_size(input_val)
            assert (
                result == expected
            ), f"_normalize_size({input_val!r}) = {result!r}, expected {expected!r}"
            assert result in valid_sizes, f"_normalize_size produced invalid size: {result}"

    def test_normalize_status_produces_valid_values(self):
        """Test that _normalize_status produces only valid Status enum values."""
        test_cases = [
            ("Available", "AVAILABLE"),
            ("available", "AVAILABLE"),
            ("ADOPTED", "ADOPTED"),
            ("Pending", "PENDING"),
            ("Hold", "HOLD"),
            ("", "UNKNOWN"),
            (None, "UNKNOWN"),
            ("invalid", "UNKNOWN"),
        ]

        valid_statuses = set(get_normalized_statuses())

        for input_val, expected in test_cases:
            result = _normalize_status(input_val)
            assert (
                result == expected
            ), f"_normalize_status({input_val!r}) = {result!r}, expected {expected!r}"
            assert result in valid_statuses, f"_normalize_status produced invalid status: {result}"

    def test_normalize_age_years_produces_numbers(self):
        """Test that _normalize_age_years produces valid number values."""
        test_cases = [
            ("3 years", 3.0),
            ("2 years 6 months", 2.5),
            ("1 year", 1.0),
            ("6 months", 0.5),
            ("", 0.0),
            (None, 0.0),
            ("invalid", 0.0),
        ]

        for input_val, expected in test_cases:
            result = _normalize_age_years(input_val)
            assert isinstance(
                result, float
            ), f"_normalize_age_years should return float, got {type(result)}"
            assert (
                result == expected
            ), f"_normalize_age_years({input_val!r}) = {result}, expected {expected}"

    def test_build_age_display_produces_strings(self):
        """Test that _build_age_display produces valid string values."""
        test_cases = [
            (3.0, "3 years"),
            (2.5, "2 years 6 months"),
            (1.0, "1 year"),
            (0.5, "6 months"),
            (0.0, "Unknown"),
            (-1.0, "Unknown"),
        ]

        for input_val, expected in test_cases:
            result = _build_age_display(input_val)
            assert isinstance(
                result, str
            ), f"_build_age_display should return string, got {type(result)}"
            assert (
                result == expected
            ), f"_build_age_display({input_val}) = {result!r}, expected {expected!r}"


class TestSchemaValidation:
    """Test that schema validation works with realistic dog data."""

    def test_valid_minimal_dog_record_passes_validation(self):
        """Test that a minimal valid dog record passes schema validation."""
        minimal_dog = {
            "Internal-ID": "123",
            "ID": "EXT-123",
            "Name": "Test Dog",
            "Status": "AVAILABLE",
            "AgeYears": 2.0,
            "AgeDisplay": "2 years",
            "IsInCustody": True,
            "IsAvailableForAdoption": True,
            "IsHospice": False,
            "IsEventDog": False,
            "PersonalityNotes": "",
            "IntakeNotes": "",
            "MedicalNotes": "",
        }

        # Should not raise an exception
        validate_dog_record(minimal_dog)

    def test_valid_complete_dog_record_passes_validation(self):
        """Test that a complete valid dog record passes schema validation."""
        complete_dog = {
            "Internal-ID": "123",
            "ID": "EXT-123",
            "Name": "Buddy",
            "Breed": "Golden Retriever",
            "AgeYears": 3.5,
            "AgeDisplay": "3 years 6 months",
            "Size": "Large",
            "Gender": "Male",
            "Status": "AVAILABLE",
            "Description": "Friendly dog looking for a home",
            "Photos": ["https://example.com/photo1.jpg", "https://example.com/photo2.jpg"],
            "CaseManager": "Jane Smith",
            "MemosRawHTML": "<p>Some memo content</p>",
            "PersonalityNotes": "Friendly and energetic",
            "IntakeNotes": "Found as stray",
            "MedicalNotes": "Up to date on vaccinations",
            "AdoptionCategory": "Adult",
            "MedicalCategory": "Healthy",
            "BehaviorCategory": "Good with dogs",
            "FullAnimalProfile": "Complete profile text",
            "Treatments": [
                {"date": "2024-01-01", "treatment": "Vaccination", "notes": "Rabies shot"}
            ],
            "IntakeDate": "2024-01-01",
            "Location": "Main Shelter",
            "Stage": "Ready for Adoption",
            "Weight": "65.5",
            "FosterName": "John Doe",
            "FosterPhone": "555-1234",
            "FosterEmail": "john@example.com",
            "ScrapeError": "",
            "IsInCustody": True,
            "IsAvailableForAdoption": True,
            "IsHospice": False,
            "IsEventDog": False,
        }

        # Should not raise an exception
        validate_dog_record(complete_dog)

    def test_invalid_dog_record_fails_validation(self):
        """Test that invalid dog records fail schema validation."""
        invalid_dog = {
            "Internal-ID": "123",
            "ID": "EXT-123",
            "Name": "Test Dog",
            "Status": "INVALID_STATUS",  # Invalid enum value
            "AgeYears": 2.0,
            "AgeDisplay": "2 years",
            "IsInCustody": True,
            "IsAvailableForAdoption": True,
            "IsHospice": False,
            "IsEventDog": False,
            "PersonalityNotes": "",
            "IntakeNotes": "",
            "MedicalNotes": "",
        }

        with pytest.raises(SchemaValidationError):
            validate_dog_record(invalid_dog)

    def test_missing_required_field_fails_validation(self):
        """Test that dog records missing required fields fail validation."""
        incomplete_dog = {
            "Internal-ID": "123",
            # Missing "ID" which is required
            "Name": "Test Dog",
            "Status": "AVAILABLE",
            "AgeYears": 2.0,
            "AgeDisplay": "2 years",
            "IsInCustody": True,
            "IsAvailableForAdoption": True,
            "IsHospice": False,
            "IsEventDog": False,
            "PersonalityNotes": "",
            "IntakeNotes": "",
            "MedicalNotes": "",
        }

        with pytest.raises(SchemaValidationError):
            validate_dog_record(incomplete_dog)

    def test_wrong_type_fails_validation(self):
        """Test that dog records with wrong field types fail validation."""
        wrong_type_dog = {
            "Internal-ID": "123",
            "ID": "EXT-123",
            "Name": "Test Dog",
            "Status": "AVAILABLE",
            "AgeYears": "2.0",  # Should be number, not string
            "AgeDisplay": "2 years",
            "IsInCustody": True,
            "IsAvailableForAdoption": True,
            "IsHospice": False,
            "IsEventDog": False,
            "PersonalityNotes": "",
            "IntakeNotes": "",
            "MedicalNotes": "",
        }

        with pytest.raises(SchemaValidationError):
            validate_dog_record(wrong_type_dog)

    def test_boolean_fields_must_be_boolean(self):
        """Test that boolean fields must actually be boolean values."""
        wrong_boolean_dog = {
            "Internal-ID": "123",
            "ID": "EXT-123",
            "Name": "Test Dog",
            "Status": "AVAILABLE",
            "AgeYears": 2.0,
            "AgeDisplay": "2 years",
            "IsInCustody": "true",  # Should be boolean, not string
            "IsAvailableForAdoption": True,
            "IsHospice": False,
            "IsEventDog": False,
            "PersonalityNotes": "",
            "IntakeNotes": "",
            "MedicalNotes": "",
        }

        with pytest.raises(SchemaValidationError):
            validate_dog_record(wrong_boolean_dog)

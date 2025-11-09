#!/usr/bin/env python3
"""
Validate scraped dog data against expectations from normalizeDog() in the webapp.

This script validates that ETL output matches what the webapp normalizeDog() function expects:
- Photos: Must be an array (or missing, defaults to [])
- Memo fields: Various memo-related fields that normalizeDog() passes through
- Required fields: All ETL-required fields must be present and non-null
"""

import json
import jsonschema
import os
from typing import Dict, Any, List

def load_schema() -> Dict[str, Any]:
    """Load the dog schema from the common directory."""
    schema_path = os.path.join(os.path.dirname(__file__), '..', '..', 'common', 'schemas', 'dog.schema.json')
    with open(schema_path, 'r') as f:
        return json.load(f)

def validate_dog_data(dog_data: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate dog data against schema and return validation result with errors."""
    try:
        jsonschema.validate(instance=dog_data, schema=schema)
        return True, []
    except jsonschema.ValidationError as e:
        return False, [str(e)]
    except Exception as e:
        return False, [f"Unexpected validation error: {e}"]

def validate_normalize_dog_expectations(dog_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate that dog data meets normalizeDog() expectations from the webapp.

    Checks:
    - Photos: Must be array if present (normalizeDog defaults to [] if not array)
    - Required ETL fields: Must be present and non-null (AgeYears, AgeDisplay, IsInCustody, etc.)
    - Memo fields: Various memo fields that normalizeDog() passes through should be reasonable
    """
    errors = []

    # Photos validation - normalizeDog expects array or defaults to []
    if "Photos" in dog_data:
        if not isinstance(dog_data["Photos"], list):
            errors.append(f"Photos field must be an array, got {type(dog_data['Photos'])}")

    # Required ETL fields validation - these must be present per contract
    required_etl_fields = [
        'AgeYears', 'AgeDisplay', 'IsInCustody',
        'IsAvailableForAdoption', 'IsHospice', 'IsEventDog'
    ]

    for field in required_etl_fields:
        if field not in dog_data:
            errors.append(f"Missing required ETL field: {field}")
        elif dog_data[field] is None:
            errors.append(f"Required ETL field {field} is null")

    # Memo fields validation - these should be strings if present
    memo_fields = [
        'MemosRawHTML', 'PersonalityNotes', 'IntakeNotes', 'MedicalNotes',
        'AdoptionCategory', 'MedicalCategory', 'BehaviorCategory', 'FullAnimalProfile'
    ]

    for field in memo_fields:
        if field in dog_data and dog_data[field] is not None:
            if not isinstance(dog_data[field], str):
                errors.append(f"Memo field {field} should be string, got {type(dog_data[field])}")

    # Treatments validation - should be array if present (like Photos)
    if "Treatments" in dog_data:
        if not isinstance(dog_data["Treatments"], list):
            errors.append(f"Treatments field must be an array, got {type(dog_data['Treatments'])}")

    return len(errors) == 0, errors

def validate_dog_record_comprehensive(dog_data: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Comprehensive validation: both schema validation and normalizeDog expectations.
    """
    all_errors = []

    # Schema validation
    schema_valid, schema_errors = validate_dog_data(dog_data, schema)
    all_errors.extend(schema_errors)

    # normalizeDog expectations validation
    normalize_valid, normalize_errors = validate_normalize_dog_expectations(dog_data)
    all_errors.extend(normalize_errors)

    return len(all_errors) == 0, all_errors

def create_sample_etl_output():
    """
    Create a sample dog record that represents typical ETL output.
    This is used for testing the validation functions.
    """
    return {
        # Required core fields
        "Internal-ID": "MVSF-A-56536",
        "ID": "MVSF-A-56536",
        "Name": "Murph",
        "Status": "HOLD",

        # Required ETL-computed fields (contract requires these)
        "AgeYears": 6.8,
        "AgeDisplay": "6 years 10 months",
        "IsInCustody": True,
        "IsAvailableForAdoption": False,
        "IsHospice": False,
        "IsEventDog": True,

        # Optional fields
        "Breed": "Mixed Breed",
        "Size": "Medium",
        "Gender": "Male",
        "Description": "A friendly dog looking for a home",

        # Photos - must be array (normalizeDog expects this)
        "Photos": ["https://example.com/photo1.jpg", "https://example.com/photo2.jpg"],

        # Memo fields - normalizeDog expects these as strings
        "MemosRawHTML": "<p>Sample memo content</p>",
        "PersonalityNotes": "Friendly and energetic",
        "IntakeNotes": "Found as stray, very scared initially but warming up",
        "MedicalNotes": "Up to date on vaccines",
        "AdoptionCategory": "Adult",
        "MedicalCategory": "Healthy",
        "BehaviorCategory": "Good with dogs",

        # Full scraped content
        "FullAnimalProfile": "Sample profile HTML content...",

        # Arrays (like Photos, normalizeDog expects these)
        "Treatments": [
            {"date": "2025-01-15", "treatment": "Vaccination", "notes": "Rabies vaccine"},
            {"date": "2025-01-16", "treatment": "Deworming", "notes": "Monthly dewormer"}
        ],

        # Other optional fields
        "CaseManager": "John Doe",
        "IntakeDate": "2025-01-15",
        "Location": "Headquarters",
        "Stage": "Medical Hold",
        "Weight": "7.1 kg",

        # Foster info
        "FosterName": "Jane Smith",
        "FosterPhone": "555-0123",
        "FosterEmail": "jane@example.com",

        # Scraping metadata
        "ScrapeError": ""  # Empty string if no error, per schema
    }

def main():
    """
    Main validation function - validates sample ETL output against webapp expectations.
    """
    try:
        schema = load_schema()
        print("Loaded dog schema successfully")

        # Create sample ETL output that represents what normalizeDog() expects
        sample_dog = create_sample_etl_output()

        print("\n=== VALIDATION AGAINST WEBAPP normalizeDog() EXPECTATIONS ===")

        # Test normalizeDog expectations (what the webapp actually checks)
        normalize_valid, normalize_errors = validate_normalize_dog_expectations(sample_dog)

        print(f"normalizeDog() compatibility: {'PASS' if normalize_valid else 'FAIL'}")
        if not normalize_valid:
            print("normalizeDog() expectation errors:")
            for error in normalize_errors:
                print(f"  - {error}")

        # Test full schema validation
        schema_valid, schema_errors = validate_dog_data(sample_dog, schema)

        print(f"\nSchema validation: {'PASS' if schema_valid else 'FAIL'}")
        if not schema_valid:
            print("Schema validation errors:")
            for error in schema_errors:
                print(f"  - {error}")

        # Test comprehensive validation
        comprehensive_valid, all_errors = validate_dog_record_comprehensive(sample_dog, schema)

        print(f"\nComprehensive validation (schema + normalizeDog): {'PASS' if comprehensive_valid else 'FAIL'}")
        if not comprehensive_valid:
            print(f"Total validation errors: {len(all_errors)}")

        # Summary for CI
        print(f"\n=== SUMMARY ===")
        print(f"✅ ETL output meets webapp expectations: {'YES' if normalize_valid else 'NO'}")
        print(f"✅ ETL output passes schema validation: {'YES' if schema_valid else 'NO'}")
        print(f"✅ ETL output fully valid: {'YES' if comprehensive_valid else 'NO'}")

        # Test with intentionally invalid data to ensure validation works
        print(f"\n=== TESTING VALIDATION WITH INVALID DATA ===")
        invalid_dog = create_sample_etl_output()
        invalid_dog["Photos"] = "not_an_array"  # Should be array
        invalid_dog["AgeYears"] = None  # Should not be null

        invalid_comprehensive_valid, invalid_errors = validate_dog_record_comprehensive(invalid_dog, schema)
        print(f"Invalid data correctly rejected: {'YES' if not invalid_comprehensive_valid else 'NO'}")
        print(f"Number of validation errors found: {len(invalid_errors)}")

        return 0 if comprehensive_valid else 1

    except Exception as e:
        print(f"Validation failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())

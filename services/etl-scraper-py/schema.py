"""
Schema loading and normalization helpers for ETL pipeline.
Centralized location for all schema-related logic and field normalizations.
"""

import json
import os
from typing import Dict, Any
from jsonschema import Draft7Validator

# Load and validate dog schema
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'common', 'schemas', 'dog.schema.json')
with open(SCHEMA_PATH) as f:
    DOG_SCHEMA = json.load(f)

DOG_VALIDATOR = Draft7Validator(DOG_SCHEMA)

def _normalize_size(size: str) -> str:
    """Normalize ShelterLuv size format to schema-compliant format."""
    if not size or not isinstance(size, str) or size.strip() == '':
        return 'UNKNOWN'  # Don't lie about missing data

    size_lower = size.lower().strip()

    # Map ShelterLuv formats to schema formats
    if 'small' in size_lower:
        return 'Small'
    elif 'medium' in size_lower:
        return 'Medium'
    elif 'large' in size_lower:
        if 'x-large' in size_lower or 'extra' in size_lower:
            return 'X-Large'
        else:
            return 'Large'

    # If no match, indicate unknown rather than guessing
    return 'UNKNOWN'

def _normalize_status(status: str) -> str:
    """
    Normalize ShelterLuv status format to schema-compliant format.

    CONTRACT: This function MUST only return one of the following values:
    - 'AVAILABLE': Dog is available for adoption
    - 'PENDING': Adoption application in progress
    - 'HOLD': Temporarily unavailable (medical, behavioral, etc.)
    - 'ADOPTED': Successfully adopted
    - 'UNKNOWN': Status could not be determined

    These values are defined in the dog.schema.json enum and must remain synchronized.
    Frontend statusMapping.js depends on these exact values.
    """
    if not status or not isinstance(status, str):
        return 'UNKNOWN'

    status_lower = status.lower().strip()

    # Map ShelterLuv status values to schema values
    if 'available' in status_lower:
        return 'AVAILABLE'
    elif 'pending' in status_lower:
        return 'PENDING'
    elif 'hold' in status_lower:
        return 'HOLD'
    elif 'adopted' in status_lower or 'serviced out' in status_lower:
        return 'ADOPTED'
    elif 'transferred' in status_lower or 'healthy in home' in status_lower:
        return 'ADOPTED'
    else:
        return 'UNKNOWN'


def _normalize_age_years(age_string: str) -> float:
    """
    Extract numeric age in years from ShelterLuv age string.
    Handles formats like "3 years", "6 months", "2 years 3 months", etc.
    Returns age as float (e.g., 3.5 for 3 years 6 months).

    If age_string is missing/invalid, return 0.0 (Unknown).
    """
    if not age_string or not isinstance(age_string, str):
        return 0.0

    age_str = age_string.lower().strip()

    # Handle common ShelterLuv formats
    years = 0.0
    months = 0.0

    # Extract years
    if 'year' in age_str:
        import re
        year_match = re.search(r'(\d+)\s*year', age_str)
        if year_match:
            years = float(year_match.group(1))

    # Extract months
    if 'month' in age_str:
        import re
        month_match = re.search(r'(\d+)\s*month', age_str)
        if month_match:
            months = float(month_match.group(1))

    # Convert months to years and add
    total_years = years + (months / 12.0)

    # Round to 1 decimal place for reasonable precision
    return round(total_years, 1) if total_years > 0 else 0.0

def _build_age_display(age_years: float) -> str:
    """
    Build human-readable age display string from numeric age in years.
    Returns 'Unknown' for age_years = 0.0.
    """
    if age_years <= 0:
        return "Unknown"

    if age_years < 1:
        months = int(age_years * 12)
        return f"{months} month{'s' if months != 1 else ''}"

    years = int(age_years)
    months = int((age_years - years) * 12)

    if months == 0:
        return f"{years} year{'s' if years != 1 else ''}"
    else:
        return f"{years} year{'s' if years != 1 else ''} {months} month{'s' if months != 1 else ''}"

def get_normalized_statuses() -> list:
    """
    Return the list of valid normalized statuses from the schema.
    This is the single source of truth for valid status values.
    Frontend and tests should use this to stay in sync with schema.
    """
    return DOG_SCHEMA["properties"]["Status"]["enum"]


def get_required_fields() -> list:
    """
    Return the list of required fields from the schema.
    This is the single source of truth for required dog fields.
    ETL validation and dev scripts should use this to stay in sync.
    """
    return DOG_SCHEMA.get("required", [])


def get_validator():
    """
    Return the JSON schema validator for dog records.
    Use this instead of accessing DOG_VALIDATOR directly to maintain abstraction.
    """
    return DOG_VALIDATOR


def validate_dog_record(dog_dict: Dict[str, Any]) -> None:
    """Validate a dog record against the schema. Raises SchemaValidationError on failure."""
    from errors import SchemaValidationError
    errors = sorted(DOG_VALIDATOR.iter_errors(dog_dict), key=lambda e: e.path)
    if errors:
        raise SchemaValidationError(f"Schema validation failed for dog {dog_dict.get('Internal-ID')}: {errors[0].message}")


def assert_size_order_matches_schema() -> None:
    """
    Assert that the Size enum in the schema is properly ordered for display.
    This is called during ETL startup to ensure the schema Size enum follows expected ordering.
    """
    schema_sizes = DOG_SCHEMA["properties"]["Size"]["enum"]
    expected_order = ["Small", "Medium", "Large", "X-Large", "UNKNOWN"]

    if schema_sizes != expected_order:
        raise ValueError(
            f"Schema Size enum does not match expected order. "
            f"Expected: {expected_order}, Got: {schema_sizes}"
        )

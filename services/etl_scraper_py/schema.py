"""
Schema loading and normalization helpers for ETL pipeline.
Centralized location for all schema-related logic and field normalizations.
"""

import json
import os
from typing import Any, Dict

from jsonschema import Draft7Validator

# Schema will be loaded lazily when first accessed
_DOG_SCHEMA = None
_DOG_VALIDATOR = None


def _get_dog_schema() -> Dict[str, Any]:
    """Load and return the dog schema, caching it for subsequent calls."""
    global _DOG_SCHEMA
    if _DOG_SCHEMA is None:
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "common", "schemas", "dog.schema.json"
        )
        with open(schema_path) as f:
            _DOG_SCHEMA = json.load(f)
    return _DOG_SCHEMA


def _get_dog_validator() -> Draft7Validator:
    """Load and return the dog validator, caching it for subsequent calls."""
    global _DOG_VALIDATOR
    if _DOG_VALIDATOR is None:
        _DOG_VALIDATOR = Draft7Validator(_get_dog_schema())
    return _DOG_VALIDATOR


def _normalize_size(size: str) -> str:
    """Normalize ShelterLuv size format to schema-compliant format."""
    if not size or not isinstance(size, str) or size.strip() == "":
        return "UNKNOWN"  # Don't lie about missing data

    size_lower = size.lower().strip()

    # Map ShelterLuv formats to schema formats
    if "small" in size_lower:
        return "Small"
    elif "medium" in size_lower:
        return "Medium"
    elif "large" in size_lower:
        if "x-large" in size_lower or "extra" in size_lower:
            return "X-Large"
        else:
            return "Large"

    # If no match, indicate unknown rather than guessing
    return "UNKNOWN"


# Status normalization keyword sets (pattern-driven mapping)
# These encode domain rules for mapping ShelterLuv status strings to normalized values
_AVAILABLE_KEYWORDS = [
    "available",
    "foster available",
    "headquarters available",
    "hospice available",
]
_PENDING_KEYWORDS = [
    "pending",
    "under adoption",
    "pending adoption",
    "pending medical",
    "pending behavioral",
]
_HOLD_KEYWORDS = ["hold", "on hold"]
_ADOPTED_KEYWORDS = ["adopted", "serviced out", "transferred", "healthy in home"]

# Exception table for genuinely weird cases that don't fit patterns
_STATUS_EXCEPTIONS = {
    "not available": "UNKNOWN",  # Explicitly not available (different from HOLD)
    "deceased": "UNKNOWN",
    "returned": "UNKNOWN",
}


def _normalize_status(status: str) -> str:
    """
    Normalize ShelterLuv status format to schema-compliant format using pattern-driven mapping.

    CONTRACT: This function MUST only return one of the following values:
    - 'AVAILABLE': Dog is available for adoption
    - 'PENDING': Adoption application in progress
    - 'HOLD': Temporarily unavailable (medical, behavioral, etc.)
    - 'ADOPTED': Successfully adopted
    - 'UNKNOWN': Status could not be determined

    These values are defined in the dog.schema.json enum and must remain synchronized.
    Frontend statusMapping.js depends on these exact values.

    Uses keyword pattern matching with priority: exceptions > ADOPTED > AVAILABLE > PENDING > HOLD
    """
    if not status or not isinstance(status, str):
        return "UNKNOWN"

    status_lower = status.lower().strip()

    # Check exceptions first (exact matches for weird cases)
    if status_lower in _STATUS_EXCEPTIONS:
        return _STATUS_EXCEPTIONS[status_lower]

    # Pattern matching with priority order
    # ADOPTED has highest priority (terminal status)
    for keyword in _ADOPTED_KEYWORDS:
        if keyword in status_lower:
            return "ADOPTED"

    # AVAILABLE (common case)
    for keyword in _AVAILABLE_KEYWORDS:
        if keyword in status_lower:
            return "AVAILABLE"

    # PENDING (adoption in progress)
    for keyword in _PENDING_KEYWORDS:
        if keyword in status_lower:
            return "PENDING"

    # HOLD (temporary unavailability)
    for keyword in _HOLD_KEYWORDS:
        if keyword in status_lower:
            return "HOLD"

    # No match - return UNKNOWN
    return "UNKNOWN"


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
    if "year" in age_str:
        import re

        year_match = re.search(r"(\d+)\s*year", age_str)
        if year_match:
            years = float(year_match.group(1))

    # Extract months
    if "month" in age_str:
        import re

        month_match = re.search(r"(\d+)\s*month", age_str)
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
    return _get_dog_schema()["properties"]["Status"]["enum"]


def get_normalized_sizes() -> list:
    """
    Return the list of valid normalized sizes from the schema.
    This is the single source of truth for valid size values.
    Frontend and tests should use this to stay in sync with schema.
    """
    return _get_dog_schema()["properties"]["Size"]["enum"]


def get_required_fields() -> list:
    """
    Return the list of required fields from the schema.
    This is the single source of truth for required dog fields.
    ETL validation and dev scripts should use this to stay in sync.
    """
    return _get_dog_schema().get("required", [])


def get_validator():
    """
    Return the JSON schema validator for dog records.
    Use this instead of accessing DOG_VALIDATOR directly to maintain abstraction.
    """
    return _get_dog_validator()


def validate_dog_record(dog_dict: Dict[str, Any]) -> None:
    """Validate a dog record against the schema. Raises SchemaValidationError on failure."""
    from errors import SchemaValidationError

    errors = sorted(_get_dog_validator().iter_errors(dog_dict), key=lambda e: e.path)
    if errors:
        raise SchemaValidationError(f"Schema validation failed for dog {dog_dict.get('Internal-ID')}: {errors[0].message}")


def assert_size_order_matches_schema() -> None:
    """
    Assert that the Size enum in the schema matches the expected size ordering.
    This ensures consistency between schema and generated Python artifacts.
    """
    try:
        # Import the size ordering from schema_artifact
        from schema_artifact import get_size_ordering
        expected_order = get_size_ordering()
    except ImportError:
        # Fallback to hardcoded order if schema_artifact not available
        expected_order = ["Small", "Medium", "Large", "X-Large", "UNKNOWN"]

    schema_sizes = _get_dog_schema()["properties"]["Size"]["enum"]

    if schema_sizes != expected_order:
        raise ValueError(
            f"Schema Size enum does not match expected size ordering. "
            f"Expected: {expected_order}, Got: {schema_sizes}. "
            f"Please regenerate schema artifacts with: npm run schema:gen"
        )

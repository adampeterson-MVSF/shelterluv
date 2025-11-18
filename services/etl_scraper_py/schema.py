"""
Schema loading and normalization helpers for ETL pipeline.
Centralized location for all schema-related logic and field normalizations.

This module now uses the NESTED dog schema as the canonical schema.
The old flat schema has been removed to eliminate dual schema maintenance.
"""

import json
import os
from typing import Any, Dict

from jsonschema import Draft7Validator

# Nested schema will be loaded lazily when first accessed
_DOG_SCHEMA_NESTED = None
_DOG_VALIDATOR_NESTED = None


def _get_dog_schema_nested() -> Dict[str, Any]:
    """Load and return the nested dog schema, caching it for subsequent calls."""
    global _DOG_SCHEMA_NESTED
    if _DOG_SCHEMA_NESTED is None:
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "common", "schemas", "dog.schema.nested.json"
        )
        with open(schema_path) as f:
            _DOG_SCHEMA_NESTED = json.load(f)
    return _DOG_SCHEMA_NESTED


def _get_dog_validator_nested() -> Draft7Validator:
    """Load and return the nested dog validator, caching it for subsequent calls."""
    global _DOG_VALIDATOR_NESTED
    if _DOG_VALIDATOR_NESTED is None:
        _DOG_VALIDATOR_NESTED = Draft7Validator(_get_dog_schema_nested())
    return _DOG_VALIDATOR_NESTED


# Status normalization keyword sets (moved from dog_schema.py to maintain single source of truth)
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
    "not available": "unknown",  # Explicitly not available (different from HOLD)
    "deceased": "unknown",
    "returned": "unknown",
}


def normalize_status(status: str) -> str:
    """
    Normalize ShelterLuv status format to schema-compliant format using pattern-driven mapping.

    CONTRACT: This function MUST only return one of the following values:
    - 'available': Dog is available for adoption
    - 'pending': Adoption application in progress
    - 'hold': Temporarily unavailable (medical, behavioral, etc.)
    - 'adopted': Successfully adopted
    - 'unknown': Status could not be determined

    These values are defined in the nested dog schema enum and must remain synchronized.
    Frontend statusMapping.js depends on these exact values.

    Uses keyword pattern matching with priority: exceptions > ADOPTED > AVAILABLE > PENDING > HOLD
    """
    if not status or not isinstance(status, str):
        return "unknown"

    status_lower = status.lower().strip()

    # Check exceptions first (exact matches for weird cases)
    if status_lower in _STATUS_EXCEPTIONS:
        return _STATUS_EXCEPTIONS[status_lower]

    # Pattern matching with priority order
    # ADOPTED has highest priority (terminal status)
    for keyword in _ADOPTED_KEYWORDS:
        if keyword in status_lower:
            return "adopted"

    # AVAILABLE (common case)
    for keyword in _AVAILABLE_KEYWORDS:
        if keyword in status_lower:
            return "available"

    # PENDING (adoption in progress)
    for keyword in _PENDING_KEYWORDS:
        if keyword in status_lower:
            return "pending"

    # HOLD (temporary unavailability)
    for keyword in _HOLD_KEYWORDS:
        if keyword in status_lower:
            return "hold"

    # No match - return UNKNOWN
    return "unknown"


def get_validator():
    """
    Return the JSON schema validator for nested dog records.
    Use this instead of accessing _DOG_VALIDATOR_NESTED directly to maintain abstraction.
    """
    return _get_dog_validator_nested()


def validate_dog_record(dog_dict: Dict[str, Any]) -> None:
    """Validate a dog record against the nested schema. Raises SchemaValidationError on failure."""
    from errors import SchemaValidationError

    errors = sorted(_get_dog_validator_nested().iter_errors(dog_dict), key=lambda e: e.path)
    if errors:
        raise SchemaValidationError(f"Schema validation failed for dog {dog_dict.get('internalId')}: {errors[0].message}")

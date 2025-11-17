"""
Foster and event enrichment logic for ETL pipeline.
Handles building foster mappings and enriching dog records with external data.
"""

from typing import Any, Dict, List, Mapping

from flags import compute_derived_flags
from foster_mapping import build_event_maps, build_foster_maps

# Import separated concerns
from normalization import normalize_basic_fields
from schema import (
    _build_age_display,
    _get_dog_schema,
    _normalize_age_years,
    _normalize_size,
    _normalize_status,
    validate_dog_record,
)


def build_dog_record(
    api_animal: Mapping[str, Any],
    scraped: Mapping[str, Any],
    foster_info: Dict[str, Any] = None,
    event_info: Dict[str, Any] = None,
    memo_html: str = "",
) -> dict:
    """Build validated dog record. Multiple focused passes."""

    # Assert required IDs exist early
    if not api_animal.get("Internal-ID") or not api_animal.get("ID"):
        from errors import SchemaValidationError

        raise SchemaValidationError(f"Missing required Internal-ID or ID for dog record")

    # Pass 1: Merge all data sources
    merged = _merge_data_sources(api_animal, scraped, foster_info, event_info, memo_html)

    # Pass 2: Normalize basic fields (age, size, status)
    normalized = normalize_basic_fields(merged)

    # Pass 3: Compute derived flags
    flagged = compute_derived_flags(normalized)

    # Pass 4: Parse structured notes from memos
    noted = _parse_structured_notes(flagged)

    # Pass 5: Validate and filter to schema
    valid = _validate_and_filter(noted)

    return valid


def _merge_data_sources(
    api_animal: Mapping[str, Any],
    scraped: Mapping[str, Any],
    foster_info: Dict[str, Any] = None,
    event_info: Dict[str, Any] = None,
    memo_html: str = "",
) -> Dict[str, Any]:
    """Merge all data sources into a single dict."""
    merged = {**api_animal, **scraped, **(foster_info or {}), **(event_info or {})}

    # For critical fields, prefer valid scraped values over invalid API values
    critical_fields = ["Status", "Name", "ID"]
    for field in critical_fields:
        api_value = api_animal.get(field, "")
        scraped_value = scraped.get(field, "")

        # If API value is empty/invalid and scraped value is valid, use scraped value
        if (not api_value or api_value == "" or api_value == "UNKNOWN") and scraped_value and scraped_value != "":
            merged[field] = scraped_value


    if memo_html:
        merged["MemosRawHTML"] = memo_html
    return merged


def _parse_structured_notes(dog: Dict[str, Any]) -> Dict[str, Any]:
    """Parse structured notes from raw HTML memos."""
    result = dict(dog)

    if result.get("MemosRawHTML"):
        from scraper.parsers import parse_memos_by_type_pure

        notes = parse_memos_by_type_pure(result["MemosRawHTML"])
        result.update(notes)
    else:
        # Ensure we don't accidentally reuse old notes when memos are not scraped
        result.setdefault("PersonalityNotes", "")
        result.setdefault("IntakeNotes", "")
        result.setdefault("MedicalNotes", "")

    return result


def _validate_and_filter(normalized: Dict[str, Any]) -> Dict[str, Any]:
    """Filter to schema keys and validate."""
    # Filter to allowed keys
    ALLOWED_KEYS = set(_get_dog_schema()["properties"].keys())
    filtered = {k: v for k, v in normalized.items() if k in ALLOWED_KEYS}

    # Sanity check: ensure AgeYears required by schema is present
    if "AgeYears" not in filtered:
        # This should never happen after normalization fix
        from errors import SchemaValidationError

        raise SchemaValidationError(
            f"Internal ETL bug: AgeYears missing after normalization for dog {normalized.get('Internal-ID')}"
        )

    # Handle null values for all fields before validation
    schema_properties = _get_dog_schema()["properties"]

    for field_name, field_value in filtered.items():
        if field_value is None:
            field_type = schema_properties.get(field_name, {}).get("type")
            if field_type == "string":
                filtered[field_name] = ""  # Convert null strings to empty strings
            elif field_type == "boolean":
                filtered[field_name] = False  # Convert null booleans to false
            elif field_type == "number":
                filtered[field_name] = 0  # Convert null numbers to 0

    # Special handling for Status field - ensure it's always valid
    if "Status" in filtered:
        status_value = filtered["Status"]
        if not status_value or status_value not in ["AVAILABLE", "ADOPTED", "PENDING", "HOLD", "UNKNOWN"]:
            # If Status is empty, invalid, or missing, default to AVAILABLE for in-custody dogs
            filtered["Status"] = "AVAILABLE"

    # Special handling for Gender field - handle invalid enum values
    if "Gender" in filtered:
        gender_value = filtered["Gender"]
        if gender_value and gender_value not in ["Male", "Female"]:
            # If Gender is invalid (like "Unknown"), remove it since it's not required
            del filtered["Gender"]

    # Ensure all required fields exist
    from schema import get_required_fields
    required_fields = get_required_fields()
    for field in required_fields:
        if field not in filtered:
            field_type = schema_properties.get(field, {}).get("type")
            if field_type == "string":
                filtered[field] = ""  # Default missing strings to empty
            elif field_type == "boolean":
                filtered[field] = False  # Default missing booleans to false
            elif field_type == "number":
                filtered[field] = 0  # Default missing numbers to 0

    # Validate
    validate_dog_record(filtered)

    # Assert ETL-required fields exist (fail fast if ETL logic is broken)
    from schema import get_required_fields

    required_etl_fields = get_required_fields()
    for field in required_etl_fields:
        if field not in filtered:
            from errors import SchemaValidationError

            raise SchemaValidationError(
                f"ETL-required field '{field}' missing after validation - ETL logic error"
            )

        # Additional validation for boolean flags
        if field in ["IsInCustody", "IsAvailableForAdoption", "IsHospice", "IsEventDog"]:
            value = filtered[field]
            if not isinstance(value, bool):
                from errors import SchemaValidationError

                raise SchemaValidationError(
                    f"ETL flag '{field}' must be boolean, got {type(value).__name__}: {value}"
                )

    return filtered

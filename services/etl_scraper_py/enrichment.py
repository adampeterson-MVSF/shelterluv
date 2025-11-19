"""
Foster and event enrichment logic for ETL pipeline.
Handles building foster mappings and enriching dog records with external data.
"""

from typing import Any, Dict, List, Mapping
from dog_types import Dog

from flags import compute_derived_flags
from foster_mapping import build_event_maps, build_foster_maps

# Import separated concerns
from normalization import normalize_basic_fields
from schema import (
    _get_dog_schema_nested as _get_dog_schema,
    validate_dog_record,
)
from dog_schema import _normalize_status
from normalization import (
    _build_age_display,
    _normalize_age_years,
    _normalize_size,
)
from schema_artifact import SCHEMA_ARTIFACT

# Field ownership metadata for merge decisions
_FIELD_OWNERSHIP = SCHEMA_ARTIFACT.get("fieldOwnership", {})

# Get valid schema field names for validation
_SCHEMA_PROPERTIES = SCHEMA_ARTIFACT.get("properties", {})


def _is_missing(value: Any) -> bool:
    """Check if a value is considered missing/empty."""
    return value is None or value == "" or value == [] or value == {}


def _is_valid_schema_field(field_name: str) -> bool:
    """Check if a field name is valid according to the JSON schema."""
    return field_name in _SCHEMA_PROPERTIES


def build_dog_record(
    api_animal: Mapping[str, Any],
    scraped: Mapping[str, Any],
    foster_info: Dict[str, Any] = None,
    event_info: Dict[str, Any] = None,
    memo_html: str = "",
    scraped_foster_info: Dict[str, Any] = None,
) -> dict:
    """Build validated dog record. Multiple focused passes."""

    # Assert required IDs exist early
    if not api_animal.get("Internal-ID") or not api_animal.get("ID"):
        from errors import SchemaValidationError

        raise SchemaValidationError(f"Missing required Internal-ID or ID for dog record")

    # Pass 1: Merge all data sources
    merged = _merge_data_sources(api_animal, scraped, foster_info, event_info, memo_html, scraped_foster_info)

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
    scraped_foster_info: Dict[str, Any] = None,
) -> Dog:
    """Merge all data sources into a single dict.

    Rules:
    - API is authoritative for fields marked ownership=api
    - Scraper is authoritative for fields marked ownership=scraper
    - For everything else, scraper only fills in missing API values
    """

    # 1) Start with API as the base – this is the source of truth.
    # Validate that API fields are valid schema fields
    merged: Dog = {}
    for field, value in api_animal.items():
        if _is_valid_schema_field(field):
            merged[field] = value
        # Skip invalid fields silently - API might have extra fields

    # 2) Enrich with ETL-derived data (foster/events) – these don't exist in API.
    # Prioritize scraped foster info over API-derived foster info
    if scraped_foster_info:
        for field, value in scraped_foster_info.items():
            if _is_valid_schema_field(field):
                merged[field] = value
            # Log invalid fields for debugging
    elif foster_info:
        for field, value in foster_info.items():
            if _is_valid_schema_field(field):
                merged[field] = value
    if event_info:
        for field, value in event_info.items():
            if _is_valid_schema_field(field):
                merged[field] = value

    # 3) Use scraper as a patch layer, guided by fieldOwnership.
    for field, scraped_value in scraped.items():
        # MemosRawHTML handled explicitly below; don't fight with memo_html param.
        if field == "MemosRawHTML":
            continue

        owner_info = _FIELD_OWNERSHIP.get(field, {})
        owner = owner_info.get("ownership")
        api_value = merged.get(field)

        if not _is_valid_schema_field(field):
            # Skip fields that aren't in the schema
            continue

        if owner == "scraper":
            # Scraper is canonical for these; API either doesn't have them
            # or uses a type we can't consume (e.g. Attributes object vs list).
            # Always use scraped value if available, otherwise remove API value entirely.
            if not _is_missing(scraped_value):
                merged[field] = scraped_value
            elif field in merged:
                # If scraped didn't provide this scraper-owned field, remove any API value
                del merged[field]

        elif owner == "api":
            # API wins. Only let scraper fill in truly missing API values.
            if _is_missing(api_value) and not _is_missing(scraped_value):
                merged[field] = scraped_value

        else:
            # ownership = "etl" or unknown – treat scraper as a gap filler.
            if _is_missing(api_value) and not _is_missing(scraped_value):
                merged[field] = scraped_value

    # 4) Remove any scraper-owned fields that exist in API but weren't provided by scraper
    for field in list(merged.keys()):
        if field == "MemosRawHTML":
            continue

        owner_info = _FIELD_OWNERSHIP.get(field, {})
        owner = owner_info.get("ownership")

        if owner == "scraper" and field not in scraped:
            # This scraper-owned field exists in API but scraper didn't provide it
            del merged[field]

    # 5) Identity & status: still hard-pin from API when sane.
    for field in ("Status", "Name", "ID"):
        api_value = api_animal.get(field)
        if api_value and api_value != "UNKNOWN":
            merged[field] = api_value

    # 6) MemosRawHTML: explicitly set from memo_html param (API or scrape).
    if memo_html and _is_valid_schema_field("MemosRawHTML"):
        merged["MemosRawHTML"] = memo_html

    return merged


def _parse_structured_notes(dog: Dog) -> Dog:
    """Parse structured notes from raw HTML memos."""
    result = dict(dog)

    # Preserve existing PersonalityNotes, IntakeNotes, MedicalNotes that were set by structured extraction
    # (e.g., from _extract_memos_section which correctly extracts "Kennel Card / Website Memo")
    existing_personality = result.get("PersonalityNotes", "")
    existing_intake = result.get("IntakeNotes", "")
    existing_medical = result.get("MedicalNotes", "")

    if result.get("MemosRawHTML"):
        from scraper.parsers import parse_memos_by_type_pure

        notes = parse_memos_by_type_pure(result["MemosRawHTML"])
        
        # Merge parsed notes with existing notes, prioritizing existing structured extraction
        # Only use parsed notes if existing notes are empty
        if existing_personality:
            result["PersonalityNotes"] = existing_personality
        else:
            result["PersonalityNotes"] = notes.get("PersonalityNotes", "")
        
        if existing_intake:
            result["IntakeNotes"] = existing_intake
        else:
            result["IntakeNotes"] = notes.get("IntakeNotes", "")
        
        if existing_medical:
            result["MedicalNotes"] = existing_medical
        else:
            result["MedicalNotes"] = notes.get("MedicalNotes", "")
    else:
        # Ensure we don't accidentally reuse old notes when memos are not scraped
        result.setdefault("PersonalityNotes", "Not Available")
        result.setdefault("IntakeNotes", "")
        result.setdefault("MedicalNotes", "Not Available")

    return result


def _validate_and_filter(normalized: Dog) -> Dog:
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

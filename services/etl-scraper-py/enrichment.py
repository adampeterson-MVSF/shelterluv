"""
Foster and event enrichment logic for ETL pipeline.
Handles building foster mappings and enriching dog records with external data.
"""

from typing import List, Dict, Any, Mapping
from schema import validate_dog_record, _normalize_size, _normalize_status, _normalize_age_years, _build_age_display, DOG_SCHEMA

# Import separated concerns
from normalization import normalize_basic_fields
from flags import compute_derived_flags, compute_custody
from foster_mapping import build_foster_maps, build_event_maps

def build_dog_record(api_animal: Mapping[str, Any], scraped: Mapping[str, Any],
                     foster_info: Dict[str, Any] = None, event_info: Dict[str, Any] = None,
                     memo_html: str = "") -> dict:
    """Build validated dog record. Multiple focused passes."""

    # Assert required IDs exist early
    if not api_animal.get('Internal-ID') or not api_animal.get('ID'):
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


def _merge_data_sources(api_animal: Mapping[str, Any], scraped: Mapping[str, Any],
                       foster_info: Dict[str, Any] = None, event_info: Dict[str, Any] = None,
                       memo_html: str = "") -> Dict[str, Any]:
    """Merge all data sources into a single dict."""
    merged = {**api_animal, **scraped, **(foster_info or {}), **(event_info or {})}
    if memo_html:
        merged['MemosRawHTML'] = memo_html
    return merged




def _parse_structured_notes(dog: Dict[str, Any]) -> Dict[str, Any]:
    """Parse structured notes from raw HTML memos."""
    result = dict(dog)

    if result.get('MemosRawHTML'):
        from scraper.parsers import ShelterLuvParsers
        # Create a dummy parser instance for memo parsing (no browser needed for HTML parsing)
        dummy_parser = ShelterLuvParsers(None, None)
        notes = dummy_parser.parse_memos_by_type(result['MemosRawHTML'])
        result.update(notes)
    else:
        # Ensure we don't accidentally reuse old notes when memos are not scraped
        result.setdefault('PersonalityNotes', '')
        result.setdefault('IntakeNotes', '')
        result.setdefault('MedicalNotes', '')

    return result










def _validate_and_filter(normalized: Dict[str, Any]) -> Dict[str, Any]:
    """Filter to schema keys and validate."""
    # Filter to allowed keys
    ALLOWED_KEYS = set(DOG_SCHEMA["properties"].keys())
    filtered = {k: v for k, v in normalized.items() if k in ALLOWED_KEYS}

    # Sanity check: ensure AgeYears required by schema is present
    if 'AgeYears' not in filtered:
        # This should never happen after normalization fix
        from errors import SchemaValidationError
        raise SchemaValidationError(
            f"Internal ETL bug: AgeYears missing after normalization for dog {normalized.get('Internal-ID')}"
        )

    # Validate
    validate_dog_record(filtered)

    # Assert ETL-required fields exist (fail fast if ETL logic is broken)
    from schema import get_required_fields
    required_etl_fields = get_required_fields()
    for field in required_etl_fields:
        if field not in filtered:
            from errors import SchemaValidationError
            raise SchemaValidationError(f"ETL-required field '{field}' missing after validation - ETL logic error")

        # Additional validation for boolean flags
        if field in ['IsInCustody', 'IsAvailableForAdoption', 'IsHospice', 'IsEventDog']:
            value = filtered[field]
            if not isinstance(value, bool):
                from errors import SchemaValidationError
                raise SchemaValidationError(f"ETL flag '{field}' must be boolean, got {type(value).__name__}: {value}")

    return filtered



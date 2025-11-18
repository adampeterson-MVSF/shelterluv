"""
ETL transform phase: Process and enrich raw data into validated dog records.
Pure functions that transform data without side effects.
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Literal

from dog_schema import from_shelterluv_api
from errors import SchemaValidationError, ScraperError
from foster_mapping import build_event_maps, build_foster_maps
from schema import validate_dog_record

MemosMode = Literal["none", "api"]


@dataclass
class TransformConfig:
    """Configuration for the transform phase."""

    # Transform no longer handles memos or scraping - those are in extract phase
    pass


@dataclass
class TransformResult:
    """Result of the transform phase."""

    dogs: List[Dict[str, Any]]
    invalid_count: int
    scraped_count: int
    skipped_count: int


def transform(extract_result, creds: Dict[str, str], config: TransformConfig) -> TransformResult:
    """
    Transform and enrich raw extracted data into validated dog records.
    This is a pure function that takes ExtractResult and TransformConfig, returns TransformResult.
    All data fetching (memos, scraping) is now done in the extract phase.
    """
    import logging

    logger = logging.getLogger(__name__)

    if not extract_result.animals_by_id:
        return TransformResult(dogs=[], invalid_count=0, scraped_count=0, skipped_count=0)

    # Build mappings from events and people data
    foster_map = build_foster_maps(extract_result.events, extract_result.people)
    event_map = build_event_maps(extract_result.events)

    # Build dog records using data already extracted
    dogs, invalid_count = _build_dog_records(
        extract_result.animals_by_id,
        extract_result.scraped_map,
        foster_map,
        event_map,
        extract_result.memos_data,
    )

    # Calculate stats - all scraping is now done in extract phase
    scraped_count = len(extract_result.scraped_map)
    skipped_count = len(extract_result.animals_by_id) - scraped_count

    logger.info(
        f"Processed {len(dogs)} dogs, {invalid_count} invalid, {scraped_count} scraped, {skipped_count} skipped"
    )

    return TransformResult(
        dogs=dogs,
        invalid_count=invalid_count,
        scraped_count=scraped_count,
        skipped_count=skipped_count,
    )


def _build_dog_records(
    animals_by_id: Dict[str, Dict[str, Any]],
    scraped_map: Dict[str, Dict[str, Any]],
    foster_map: Dict[str, Dict[str, Any]],
    event_map: Dict[str, Dict[str, Any]],
    memos_data: Dict[str, str],
) -> tuple[List[Dict[str, Any]], int]:
    """Build validated dog records from all available data using new structured schema."""
    import logging

    logger = logging.getLogger(__name__)

    dogs = []
    invalid_count = 0

    for internal_id, animal in animals_by_id.items():
        if not internal_id:
            continue

        try:
            # Start with API data transformed to new structured schema
            dog_record = from_shelterluv_api(animal)

            # Extract foster info from scraped data if available
            scraped_data = scraped_map.get(str(internal_id), {})
            scraped_foster_info = None
            if any(key in scraped_data for key in ['foster_name', 'foster_person_id', 'foster_profile_url']):
                scraped_foster_info = {
                    k: v for k, v in scraped_data.items()
                    if k in ['foster_name', 'foster_person_id', 'foster_profile_url']
                }

            # Apply scraped data selectively (API-first approach), excluding foster info
            filtered_scraped_data = {k: v for k, v in scraped_data.items() if k not in ['foster_name', 'foster_person_id', 'foster_profile_url']}
            _apply_scraped_data(dog_record, filtered_scraped_data)

            # Apply foster/event enrichment
            _apply_foster_event_data(dog_record, foster_map.get(str(internal_id), {}), event_map.get(str(internal_id), {}), scraped_foster_info)

            # Validate against nested schema
            validate_dog_record(dog_record)

            dogs.append(dog_record)

        except Exception as e:
            logger.warning("Skipping invalid dog %s: %s", internal_id, e)
            invalid_count += 1

    return dogs, invalid_count


def _apply_scraped_data(dog_record: Dict[str, Any], scraped_data: Dict[str, Any]) -> None:
    """Apply scraped data to dog record, following API-first approach."""
    if not scraped_data:
        return

    # Attributes - scraper owned, API may have different format
    if "Attributes" in scraped_data:
        # Convert scraped attributes list to structured format
        scraped_attrs = scraped_data["Attributes"]
        if isinstance(scraped_attrs, list):
            dog_record["attributes"]["raw"] = [
                {
                    "attributeName": attr,
                    "internalId": dog_record["internalId"],
                    "publish": "Yes",  # Assume scraped attributes are publishable
                }
                for attr in scraped_attrs
            ]

    # Behavioral attributes - scraper owned
    if "BehavioralAttributes" in scraped_data:
        behavioral_attrs = scraped_data["BehavioralAttributes"]
        if isinstance(behavioral_attrs, list):
            # Add to attributes.raw if not already present
            existing_names = {attr["attributeName"] for attr in dog_record["attributes"]["raw"]}
            for attr in behavioral_attrs:
                if attr not in existing_names:
                    dog_record["attributes"]["raw"].append({
                        "attributeName": attr,
                        "internalId": dog_record["internalId"],
                        "publish": "Yes",
                    })

    # Medical notes - enrich content
    if "MedicalNotes" in scraped_data and scraped_data["MedicalNotes"]:
        if dog_record["content"]["description"]:
            dog_record["content"]["description"] += f"\n\nMedical Notes: {scraped_data['MedicalNotes']}"
        else:
            dog_record["content"]["description"] = scraped_data["MedicalNotes"]

    # Personality notes - enrich content
    if "PersonalityNotes" in scraped_data and scraped_data["PersonalityNotes"]:
        if dog_record["content"]["description"]:
            dog_record["content"]["description"] += f"\n\nAbout {dog_record['name']}: {scraped_data['PersonalityNotes']}"
        else:
            dog_record["content"]["description"] = scraped_data["PersonalityNotes"]


def _apply_foster_event_data(
    dog_record: Dict[str, Any],
    foster_info: Dict[str, Any],
    event_info: Dict[str, Any],
    scraped_foster_info: Dict[str, Any] = None
) -> None:
    """Apply foster and event enrichment data."""
    # Prioritize scraped foster info over API-derived foster info
    effective_foster_info = scraped_foster_info or foster_info

    # Foster information - may override API AssociatedPerson if more complete
    if effective_foster_info:
        dog_record["foster"]["inFoster"] = True

        # Handle scraped foster info format (foster_name, foster_person_id, etc.)
        if "foster_name" in effective_foster_info:
            name = effective_foster_info["foster_name"]
            if name:
                # Simple name splitting - could be enhanced
                name_parts = name.split()
                dog_record["foster"]["person"] = {
                    "firstName": " ".join(name_parts[:-1]) if len(name_parts) > 1 else name,
                    "lastName": name_parts[-1] if len(name_parts) > 1 else "",
                    "relationshipType": "Foster",
                    "outDate": None,
                }

        # Handle API format (FosterName, FosterEmail, etc.)
        elif "FosterName" in effective_foster_info:
            name = effective_foster_info["FosterName"]
            if name:
                # Simple name splitting - could be enhanced
                name_parts = name.split()
                dog_record["foster"]["person"] = {
                    "firstName": " ".join(name_parts[:-1]) if len(name_parts) > 1 else name,
                    "lastName": name_parts[-1] if len(name_parts) > 1 else "",
                    "relationshipType": "Foster",
                    "outDate": None,
                }

        # Contact info (restricted fields) - check both formats
        email = effective_foster_info.get("FosterEmail") or effective_foster_info.get("email")
        phone = effective_foster_info.get("FosterPhone") or effective_foster_info.get("phone")

        if email and dog_record["foster"]["person"]:
            dog_record["foster"]["person"]["email"] = email
        if phone and dog_record["foster"]["person"]:
            dog_record["foster"]["person"]["phone"] = phone

        # Add person ID and profile URL if available from scraping
        if "foster_person_id" in effective_foster_info and dog_record["foster"]["person"]:
            dog_record["foster"]["person"]["personId"] = effective_foster_info["foster_person_id"]
        if "foster_profile_url" in effective_foster_info and dog_record["foster"]["person"]:
            dog_record["foster"]["person"]["profileUrl"] = effective_foster_info["foster_profile_url"]

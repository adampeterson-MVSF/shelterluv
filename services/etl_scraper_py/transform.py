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


def _convert_to_nested_schema_field_names(dog_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert from JSON schema field names (hyphenated) to nested schema field names (camelCase).
    This is necessary because from_shelterluv_api creates records with JSON schema field names,
    but validation and storage expect nested schema field names.
    """
    # Start with nested schema structure
    nested_dog = {
        "internalId": dog_record.get("Internal-ID", ""),
        "publicId": dog_record.get("ID", ""),
        "name": dog_record.get("Name", ""),
        "type": "Dog",
        "status": _normalize_status_for_nested(dog_record.get("Status", "UNKNOWN")),
        "inFoster": False,
        "lastIntakeAt": dog_record.get("IntakeDate"),
        "lastUpdatedAt": None,
        "physical": {
            "breed": dog_record.get("Breed", ""),
            "ageDays": 0,  # Would need to be calculated from DOB - placeholder
            "dob": None,  # Would need to be parsed from API data
            "sex": _normalize_sex_for_nested(dog_record.get("Gender", "Male")),
            "sizeLabel": dog_record.get("Size", "UNKNOWN"),
            "color": dog_record.get("Color", ""),
            "pattern": dog_record.get("Pattern", ""),
            "weightLbs": float(dog_record.get("Weight", 0)) if dog_record.get("Weight") else None,
            "altered": None  # Would need to be derived from medical data
        },
        "location": {
            "label": dog_record.get("Location", "")
        },
        "content": {
            "description": dog_record.get("Description", "")
        },
        "admin": {
            "caseManager": dog_record.get("CaseManager", ""),
            "intakeDate": dog_record.get("IntakeDate", ""),
            "stage": dog_record.get("Stage", ""),
            "scrapeError": dog_record.get("ScrapeError", ""),
            "adoptionPrice": dog_record.get("AdoptionPrice", ""),
            "intakeType": dog_record.get("IntakeType", ""),
            "intakeSubtype": dog_record.get("IntakeSubtype", ""),
            "outcomeType": dog_record.get("OutcomeType", ""),
            "outcomeSubtype": dog_record.get("OutcomeSubtype", ""),
            "asilomarIntake": dog_record.get("AsilomarIntake", ""),
            "asilomarOutcome": dog_record.get("AsilomarOutcome", ""),
            "jurisdictionIntake": dog_record.get("JurisdictionIntake", ""),
            "jurisdictionOutcome": dog_record.get("JurisdictionOutcome", ""),
            "previousShelterId": dog_record.get("PreviousShelterId", ""),
            "previousShelterType": dog_record.get("PreviousShelterType", ""),
            "previousShelterIssuer": dog_record.get("PreviousShelterIssuer", "")
        },
        "foster": {
            "inFoster": False,  # Will be updated by foster enrichment if dog is in foster care
            "person": None  # Will be populated by foster enrichment if available
        },
        "medical": {
            "microchipNumber": dog_record.get("MicrochipNumber", ""),
            "microchipIssuer": dog_record.get("MicrochipIssuer", ""),
            "microchipImplantDate": dog_record.get("MicrochipImplantDate", ""),
            "alteredBeforeArrival": dog_record.get("AlteredBeforeArrival", ""),
            "alteredInCare": dog_record.get("AlteredInCare", ""),
            "conditionAtIntake": dog_record.get("ConditionAtIntake", ""),
            "rabiesTagNumber": dog_record.get("RabiesTagNumber", ""),
            "microchipInfo": dog_record.get("MicrochipInfo", {}),
            "rabiesTag": dog_record.get("RabiesTag", {}),
            "microchips": []  # Will be populated from microchip data
        },
        "attributes": {
            "raw": dog_record.get("Attributes", []),
            "compatibility": {
                "cat": "unknown",
                "dog": "unknown",
                "child": "unknown"
            }
        },
        "media": {
            "coverPhoto": dog_record.get("Photos", [None])[0] if dog_record.get("Photos") else None,
            "photos": dog_record.get("Photos", [])
        },
        "source": {
            "lastIntakeUnixTime": None,  # Would be populated from API if available
            "lastUpdatedUnixTime": None,
            "dobUnixTime": None,
            "raw": {}  # Complete original API response for debugging
        }
    }

    return nested_dog


def _normalize_status_for_nested(status: str) -> str:
    """Convert JSON schema status to nested schema status format."""
    status_mapping = {
        "AVAILABLE": "available",
        "ADOPTED": "adopted",
        "PENDING": "pending",
        "HOLD": "hold",
        "UNKNOWN": "unknown"
    }
    return status_mapping.get(status, "unknown")


def _normalize_sex_for_nested(sex: str) -> str:
    """Convert JSON schema sex to nested schema sex format."""
    sex_mapping = {
        "Male": "Male",
        "Female": "Female",
        "M": "Male",
        "F": "Female"
    }
    return sex_mapping.get(sex, "Unknown")


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

            # Convert to nested schema field names before validation
            dog_record = _convert_to_nested_schema_field_names(dog_record)

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

    # Initialize nested structures if they don't exist
    if "attributes" not in dog_record:
        dog_record["attributes"] = {"raw": [], "behavioral": [], "physical": []}
    if "content" not in dog_record:
        dog_record["content"] = {}

    # Attributes - scraper owned, API may have different format
    if "Attributes" in scraped_data:
        # Convert scraped attributes list to structured format
        scraped_attrs = scraped_data["Attributes"]
        if isinstance(scraped_attrs, list):
            dog_record["attributes"]["raw"] = [
                {
                    "attributeName": attr,
                    "internalId": dog_record["Internal-ID"],
                    "publish": "Yes",  # Assume scraped attributes are publishable
                }
                for attr in scraped_attrs
            ]

    # Behavioral attributes - scraper owned
    if "BehavioralAttributes" in scraped_data:
        behavioral_attrs = scraped_data["BehavioralAttributes"]
        if isinstance(behavioral_attrs, list):
            # Initialize attributes.raw if not present
            if "raw" not in dog_record["attributes"]:
                dog_record["attributes"]["raw"] = []
            # Add to attributes.raw if not already present
            existing_names = {attr["attributeName"] for attr in dog_record["attributes"]["raw"]}
            for attr in behavioral_attrs:
                if attr not in existing_names:
                    dog_record["attributes"]["raw"].append({
                        "attributeName": attr,
                        "internalId": dog_record["Internal-ID"],
                        "publish": "Yes",
                    })

    # Medical notes - enrich content
    if "MedicalNotes" in scraped_data and scraped_data["MedicalNotes"]:
        existing_description = dog_record.get("Description", "")
        if existing_description:
            dog_record["Description"] = f"{existing_description}\n\nMedical Notes: {scraped_data['MedicalNotes']}"
        else:
            dog_record["Description"] = scraped_data["MedicalNotes"]

    # Personality notes - enrich content
    if "PersonalityNotes" in scraped_data and scraped_data["PersonalityNotes"]:
        existing_description = dog_record.get("Description", "")
        dog_name = dog_record.get("Name", "the dog")
        if existing_description:
            dog_record["Description"] = f"{existing_description}\n\nAbout {dog_name}: {scraped_data['PersonalityNotes']}"
        else:
            dog_record["Description"] = scraped_data["PersonalityNotes"]


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
                    "outDate": None,
                    "email": None,
                    "phone": None,
                    "personId": None,
                    "profileUrl": None,
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
                    "outDate": None,
                    "email": None,
                    "phone": None,
                    "personId": None,
                    "profileUrl": None,
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

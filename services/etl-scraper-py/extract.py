"""
ETL extract phase: Fetch all raw data from ShelterLuv.
Pure functions that gather data without processing it.
"""

from typing import Dict, Any, Set, List
from dataclasses import dataclass
from api import (
    get_animals_by_ids,
    get_animal_events,
    get_people
)
from scraper.in_custody_ids import scrape_in_custody_ids
import db
from errors import ApiError


@dataclass
class ExtractResult:
    """Result of the extract phase."""
    in_custody_ids: Set[str]
    animals_by_id: Dict[str, Dict[str, Any]]
    events: List[Dict[str, Any]]
    people: List[Dict[str, Any]]
    existing_metadata: Dict[str, Dict[str, Any]]  # Pre-fetched for incremental logic
    events_failed: bool = False
    people_failed: bool = False


def extract(creds: Dict[str, str], animal_limit: int | None = None, dry_run: bool = False) -> ExtractResult:
    """
    Extract all raw data needed for ETL: in-custody IDs, animals, events, people, and existing metadata.
    This is a pure function that fetches everything we know before any processing.
    """
    import logging
    import time
    logger = logging.getLogger(__name__)

    # Step 1: Scrape the in-custody IDs from ShelterLuv UI
    logger.info("Scraping in-custody animal IDs from ShelterLuv UI...")
    in_custody_ids = scrape_in_custody_ids(creds["username"], creds["password"])
    logger.info(f"Found {len(in_custody_ids)} animals currently in custody")

    # Apply limit if specified (for testing)
    if animal_limit is not None and len(in_custody_ids) > animal_limit:
        in_custody_ids = set(list(in_custody_ids)[:animal_limit])
        logger.info(f"Limited to {len(in_custody_ids)} animals for testing")

    if not in_custody_ids:
        logger.warning("No animals found in custody - nothing to process")
        return ExtractResult(
            in_custody_ids=set(),
            animals_by_id={},
            events=[],
            people=[],
            existing_metadata={}
        )

    # Step 2: Fetch full animal records using ShelterLuv IDs
    logger.info(f"Fetching {len(in_custody_ids)} animal records via ShelterLuv IDs...")
    # Use single threading to avoid rate limiting issues
    animals_by_id = get_animals_by_ids(in_custody_ids, creds["api_key"], max_workers=1)

    # Check for any missing animals
    missing_ids = in_custody_ids - set(animals_by_id.keys())
    if missing_ids:
        logger.warning(f"Failed to fetch {len(missing_ids)} animals via API: {sorted(missing_ids)}")

    if not animals_by_id:
        logger.error("No animals could be fetched from ShelterLuv API.")
        return ExtractResult(
            in_custody_ids=set(),
            animals_by_id={},
            events=[],
            people=[],
            existing_metadata={}
        )

    logger.info(f"Successfully fetched {len(animals_by_id)} animal records")

    # Step 3: Fetch events
    events_failed = False
    events = []
    try:
        events = get_animal_events(creds["api_key"])
        logger.info(f"Fetched {len(events)} events")
    except ApiError as e:
        logger.error(f"Failed to fetch events: {e}")
        events_failed = True

    # Step 4: Fetch people
    people_failed = False
    people = []
    try:
        people = get_people(creds["api_key"])
        logger.info(f"Fetched {len(people)} people")
    except ApiError as e:
        logger.error(f"Failed to fetch people: {e}")
        people_failed = True

    # Step 5: Fetch existing metadata for incremental processing
    internal_ids = list(animals_by_id.keys())
    existing_metadata = {}
    if internal_ids and not dry_run:
        existing_metadata = db.fetch_existing_metadata(internal_ids)
        logger.info(f"Fetched existing metadata for {len(existing_metadata)} animals")
    else:
        logger.info("Skipping existing metadata fetch (dry run or no animals)")

    return ExtractResult(
        in_custody_ids=in_custody_ids,
        animals_by_id=animals_by_id,
        events=events,
        people=people,
        existing_metadata=existing_metadata,
        events_failed=events_failed,
        people_failed=people_failed
    )

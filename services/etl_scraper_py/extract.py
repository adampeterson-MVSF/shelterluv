"""
ETL extract phase: Fetch all raw data from ShelterLuv.
Pure functions that gather data without processing it.
"""

from concurrency import execute_concurrent_chunks
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Set

import db
from api import get_animal_events, get_animals_by_ids, get_people
from api.api_client_memos import get_animals_memos_batch
from errors import ApiError
from scraper import ShelterLuvScraper
from scraper.in_custody_api import scrape_in_custody_ids_via_api
from scraper.in_custody_ids import scrape_in_custody_data, scrape_in_custody_ids

MemosMode = Literal["none", "api"]


@dataclass
class ExtractConfig:
    """Configuration for the extract phase.
    Defines all toggles and options - no ad-hoc boolean parameters.
    """

    memos_mode: MemosMode
    max_concurrent_scrapes: int
    animal_limit: int | None = None
    dry_run: bool = False
    skip_events_people: bool = False


def limit_animal_ids(in_custody_ids: Set[str], limit: int | None) -> Set[str]:
    """
    Apply animal limit to the in-custody IDs for testing purposes.
    Returns the limited set of IDs.
    """
    if limit is not None and len(in_custody_ids) > limit:
        return set(list(in_custody_ids)[:limit])
    return in_custody_ids


@dataclass
class ExtractResult:
    """Result of the extract phase."""

    in_custody_ids: Set[str]
    animals_by_id: Dict[str, Dict[str, Any]]
    events: List[Dict[str, Any]]
    people: List[Dict[str, Any]]
    existing_metadata: Dict[str, Dict[str, Any]]  # Pre-fetched for incremental logic
    memos_data: Dict[str, str]  # Memo HTML data by internal ID
    scraped_map: Dict[str, Dict[str, Any]]  # Scraped profile data by internal ID
    events_failed: bool = False
    people_failed: bool = False


def extract(creds: Dict[str, str], config: ExtractConfig) -> ExtractResult:
    """
    Extract all raw data needed for ETL: in-custody IDs, animals, events, people, and existing metadata.
    Pure function - all configuration comes from ExtractConfig.
    Control flow is linear: in-custody IDs → core animals → events/people → memos → scraped map.

    Args:
        creds: ShelterLuv API credentials dict
        config: ExtractConfig with all extract phase configuration
    """
    import logging
    import time

    logger = logging.getLogger(__name__)

    # Step 1: Scrape the in-custody data from ShelterLuv UI
    logger.info("Scraping in-custody animal data from ShelterLuv UI...")
    scraped_animal_data = scrape_in_custody_data(creds["username"], creds["password"])
    in_custody_ids = set(scraped_animal_data.keys())
    logger.info(f"Found {len(in_custody_ids)} animals currently in custody")

    # Apply limit if specified (for testing)
    in_custody_ids = limit_animal_ids(in_custody_ids, config.animal_limit)
    if config.animal_limit is not None and len(in_custody_ids) == config.animal_limit:
        logger.info(f"Limited to {len(in_custody_ids)} animals for testing")

        # Also limit the animals_by_id dict to match
        limited_animals_by_id = {}
        for internal_id in in_custody_ids:
            if internal_id in scraped_animal_data:
                limited_animals_by_id[internal_id] = scraped_animal_data[internal_id]
        scraped_animal_data = limited_animals_by_id

    if not in_custody_ids:
        logger.warning("No animals found in custody - nothing to process")
        return ExtractResult(
            in_custody_ids=set(),
            animals_by_id={},
            events=[],
            people=[],
            existing_metadata={},
            memos_data={},
            scraped_map={},
        )

    # Step 2: Create basic animal records from scraped UI data
    # The animal-record-summary page will provide all detailed data we need
    logger.info(f"Using {len(in_custody_ids)} animals from UI scrape (API fetch skipped)")

    # Ensure each animal record has the required Internal-ID and ID fields
    animals_by_id = {}
    for internal_id, animal_data in scraped_animal_data.items():
        # Create a clean record with required fields
        animal_record = dict(animal_data)  # Copy all scraped data
        animal_record["Internal-ID"] = internal_id  # Ensure Internal-ID is set
        # The ID field should already be in the scraped data, but ensure it's there
        if "ID" not in animal_record or not animal_record["ID"]:
            # If ID is missing, we might need to derive it from the animal name or skip
            # For now, set it to the internal_id as fallback
            animal_record["ID"] = animal_record.get("ID", internal_id)
        animals_by_id[internal_id] = animal_record

    # Step 3: Fetch events & people (for foster info - still needed)
    events_failed = False
    events = []
    if not config.skip_events_people:
        try:
            events = get_animal_events(creds["api_key"])
            logger.info(f"Fetched {len(events)} events")
        except ApiError as e:
            logger.error(f"Failed to fetch events: {e}")
            events_failed = True
    else:
        logger.info("Skipping events fetch (skip_events_people=True)")

    # Step 4: Fetch people (for foster info)
    people_failed = False
    people = []
    if not config.skip_events_people:
        try:
            people = get_people(creds["api_key"])
            logger.info(f"Fetched {len(people)} people")
        except ApiError as e:
            logger.error(f"Failed to fetch people: {e}")
            people_failed = True
    else:
        logger.info("Skipping people fetch (skip_events_people=True)")

    # Step 5: Skip existing metadata fetch for now - force fresh scraping
    internal_ids = list(animals_by_id.keys())
    existing_metadata = {}  # Empty dict means all dogs will be scraped
    logger.info("Skipping existing metadata fetch - all dogs will be scraped fresh")

    # Step 6: Scrape comprehensive data from animal record summary pages
    scraped_map = fetch_scraped_data(animals_by_id, existing_metadata, creds, config)

    return ExtractResult(
        in_custody_ids=in_custody_ids,
        animals_by_id=animals_by_id,
        events=events,
        people=people,
        existing_metadata=existing_metadata,
        memos_data={},  # Memos now come from summary page scraping
        scraped_map=scraped_map,
        events_failed=events_failed,
        people_failed=people_failed,
    )


def fetch_memos(
    animals_by_id: Dict[str, Dict[str, Any]], creds: Dict[str, str], config: ExtractConfig
) -> Dict[str, str]:
    """
    Fetch memo data from ShelterLuv API if memos_mode is enabled.
    Returns a dict mapping internal_id to memo HTML.
    """
    memos_data = {}
    if config.memos_mode == "api":
        try:
            memos_results = get_animals_memos_batch(creds["api_key"], list(animals_by_id.keys()))
            # Convert MemoResult dict to simple memos_html dict for backward compatibility
            memos_data = {
                internal_id: result.memos_html for internal_id, result in memos_results.items()
            }
        except Exception:
            # On API failure, use empty memos
            memos_data = {internal_id: "" for internal_id in animals_by_id.keys()}

    return memos_data


def fetch_scraped_data(
    animals_by_id: Dict[str, Dict[str, Any]],
    existing_metadata: Dict[str, Dict[str, Any]],
    creds: Dict[str, str],
    config: ExtractConfig,
) -> Dict[str, Dict[str, Any]]:
    """
    Filter animals that need scraping and scrape their profile data.
    Returns a dict mapping internal_id to scraped data.
    """
    import logging

    logger = logging.getLogger(__name__)

    if config.dry_run:
        logger.info("Skipping scraping in dry run mode")
        return {}

    # Filter animals that need scraping based on incremental logic
    to_scrape = _filter_animals_to_scrape(animals_by_id, existing_metadata)

    if not to_scrape:
        logger.info("No animals need scraping")
        return {}

    logger.info(f"Scraping {len(to_scrape)} animal profiles...")

    # Scrape animals concurrently
    scraped_map = _scrape_animals_concurrent(to_scrape, creds, config.max_concurrent_scrapes)

    logger.info(f"Completed scraping {len(scraped_map)} animal profiles")
    return scraped_map


def _filter_animals_to_scrape(
    animals_by_id: Dict[str, Dict[str, Any]], existing_metadata: Dict[str, Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """Filter animals that need scraping based on incremental logic."""
    import logging

    logger = logging.getLogger(__name__)

    to_scrape = {}
    for internal_id, animal in animals_by_id.items():
        animal_id = animal.get("ID")
        str_internal_id = str(internal_id)

        if not animal_id or not internal_id:
            continue

        # Check if we should skip this animal due to no changes
        should_scrape = True
        if existing_metadata:
            meta = existing_metadata.get(str_internal_id, {})
            source_updated_at = animal.get("SourceUpdatedAt", "")
            last_seen_updated = meta.get("source_updated_at", "")

            # Skip if we have metadata and the source hasn't changed
            # Since API doesn't provide "Updated" timestamp, we use SourceUpdatedAt which is set to current time on fetch
            # This means we'll always scrape unless we have a stored timestamp from a previous run
            if last_seen_updated and source_updated_at:
                # Compare timestamps - if current fetch time is same or older than last seen, skip
                # Note: Since SourceUpdatedAt is set to current time, this will only skip if we fetched
                # the same animal multiple times in the same run (unlikely but possible)
                if source_updated_at <= last_seen_updated:
                    should_scrape = False
                    logger.info(
                        f"Skipping unchanged dog {internal_id} ({animal_id}): source_updated_at={source_updated_at}, last_seen={last_seen_updated}"
                    )
                    continue
                else:
                    logger.debug(
                        f"Dog {internal_id} ({animal_id}) will be scraped: source_updated_at={source_updated_at}, last_seen={last_seen_updated}"
                    )
            elif not meta:
                logger.debug(f"No metadata found for dog {internal_id} ({animal_id}) - will scrape")
            elif not source_updated_at:
                logger.debug(
                    f"No SourceUpdatedAt for dog {internal_id} ({animal_id}) - will scrape"
                )
            elif not last_seen_updated:
                logger.debug(
                    f"No last_seen_updated for dog {internal_id} ({animal_id}) - will scrape"
                )

        if should_scrape:
            to_scrape[str_internal_id] = animal

    return to_scrape


def _scrape_animals_concurrent(
    to_scrape: Dict[str, Dict[str, Any]], creds: Dict[str, str], max_concurrent_scrapes: int
) -> Dict[str, Dict[str, Any]]:
    """Scrape animals concurrently using the specified concurrency level."""
    import logging
    import time

    logger = logging.getLogger(__name__)

    if not to_scrape:
        return {}

    if max_concurrent_scrapes <= 1:
        # Single-threaded path - REUSE BROWSER SESSION for all animals
        scraped_map = {}
        with ShelterLuvScraper(creds["username"], creds["password"]) as scraper:
            for internal_id, animal in to_scrape.items():
                animal_id = animal.get("ID")
                try:
                    logger.debug(f"Scraping {animal_id} ({internal_id})...")
                    start_time = time.time()
                    scraped = scraper.scrape_animal_record_summary(animal_id, internal_id)
                    end_time = time.time()
                    logger.info(f"Scraped {animal_id} in {end_time - start_time:.1f}s")
                    scraped_map[internal_id] = scraped
                except Exception as e:
                    logger.warning("Scrape failed for %s (%s): %s", animal_id, internal_id, e)
                    # Return minimal valid data instead of just error to prevent validation failures
                    scraped_map[internal_id] = {
                        "Internal-ID": internal_id,
                        "ID": animal_id,
                        "Status": "AVAILABLE",  # Valid default status
                        "Name": f"Scrape Failed: {animal_id}",  # Indicate the failure
                        "ScrapeError": str(e)
                    }
        return scraped_map
    else:
        # Concurrent path using shared concurrency helper
        def _scrape_chunk(items):
            """Scrape a chunk of animals using a dedicated scraper instance."""
            chunk_results = {}
            with ShelterLuvScraper(creds["username"], creds["password"]) as scraper:
                for internal_id, animal in items:
                    animal_id = animal.get("ID")
                    try:
                        logger.debug(f"Scraping {animal_id} ({internal_id}) in chunk...")
                        start_time = time.time()
                        scraped = scraper.scrape_animal_record_summary(animal_id, internal_id)
                        end_time = time.time()
                        logger.info(f"Scraped {animal_id} in {end_time - start_time:.1f}s")
                        chunk_results[internal_id] = scraped
                    except Exception as e:
                        logger.warning("Scrape failed for %s (%s): %s", animal_id, internal_id, e)
                        chunk_results[internal_id] = {"ScrapeError": str(e)}
            return chunk_results

        # Execute chunks concurrently using shared helper
        to_scrape_items = list(to_scrape.items())
        return execute_concurrent_chunks(
            items=to_scrape_items,
            process_chunk_fn=_scrape_chunk,
            max_workers=max_concurrent_scrapes
        )

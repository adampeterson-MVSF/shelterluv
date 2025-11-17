"""
ETL extract phase: Fetch all raw data from ShelterLuv.
Pure functions that gather data without processing it.
"""

from typing import Dict, Any, Set, List, Literal
from dataclasses import dataclass
from api import (
    get_animals_by_ids,
    get_animal_events,
    get_people
)
from api.api_client_memos import get_animals_memos_batch
from scraper.in_custody_ids import scrape_in_custody_ids
from scraper import ShelterLuvScraper
import db
from errors import ApiError
from concurrent.futures import ThreadPoolExecutor


MemosMode = Literal["none", "api"]


@dataclass
class ExtractConfig:
    """Configuration for the extract phase."""
    memos_mode: MemosMode
    max_concurrent_scrapes: int


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


def extract(creds: Dict[str, str], config: ExtractConfig, animal_limit: int | None = None, dry_run: bool = False, skip_events_people: bool = False) -> ExtractResult:
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
    in_custody_ids = limit_animal_ids(in_custody_ids, animal_limit)
    if animal_limit is not None and len(in_custody_ids) == animal_limit:
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
    if not skip_events_people:
        try:
            events = get_animal_events(creds["api_key"])
            logger.info(f"Fetched {len(events)} events")
        except ApiError as e:
            logger.error(f"Failed to fetch events: {e}")
            events_failed = True
    else:
        logger.info("Skipping events fetch (skip_events_people=True)")

    # Step 4: Fetch people
    people_failed = False
    people = []
    if not skip_events_people:
        try:
            people = get_people(creds["api_key"])
            logger.info(f"Fetched {len(people)} people")
        except ApiError as e:
            logger.error(f"Failed to fetch people: {e}")
            people_failed = True
    else:
        logger.info("Skipping people fetch (skip_events_people=True)")

    # Step 5: Fetch existing metadata for incremental processing
    internal_ids = list(animals_by_id.keys())
    existing_metadata = {}
    if internal_ids and not dry_run:
        existing_metadata = db.fetch_existing_metadata(internal_ids)
        logger.info(f"Fetched existing metadata for {len(existing_metadata)} animals")
    else:
        logger.info("Skipping existing metadata fetch (dry run or no animals)")

    # Step 6: Fetch memos if requested
    memos_data = fetch_memos(animals_by_id, creds, config)

    # Step 7: Filter animals that need scraping and scrape them
    scraped_map = fetch_scraped_data(animals_by_id, existing_metadata, creds, config, dry_run)

    return ExtractResult(
        in_custody_ids=in_custody_ids,
        animals_by_id=animals_by_id,
        events=events,
        people=people,
        existing_metadata=existing_metadata,
        memos_data=memos_data,
        scraped_map=scraped_map,
        events_failed=events_failed,
        people_failed=people_failed
    )


def fetch_memos(animals_by_id: Dict[str, Dict[str, Any]], creds: Dict[str, str], config: ExtractConfig) -> Dict[str, str]:
    """
    Fetch memo data from ShelterLuv API if memos_mode is enabled.
    Returns a dict mapping internal_id to memo HTML.
    """
    memos_data = {}
    if config.memos_mode == "api":
        try:
            memos_results = get_animals_memos_batch(creds["api_key"], list(animals_by_id.keys()))
            # Convert MemoResult dict to simple memos_html dict for backward compatibility
            memos_data = {internal_id: result.memos_html for internal_id, result in memos_results.items()}
        except Exception:
            # On API failure, use empty memos
            memos_data = {internal_id: "" for internal_id in animals_by_id.keys()}

    return memos_data


def fetch_scraped_data(animals_by_id: Dict[str, Dict[str, Any]], existing_metadata: Dict[str, Dict[str, Any]],
                      creds: Dict[str, str], config: ExtractConfig, dry_run: bool) -> Dict[str, Dict[str, Any]]:
    """
    Filter animals that need scraping and scrape their profile data.
    Returns a dict mapping internal_id to scraped data.
    """
    import logging
    logger = logging.getLogger(__name__)

    if dry_run:
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


def _filter_animals_to_scrape(animals_by_id: Dict[str, Dict[str, Any]], existing_metadata: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
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
            if last_seen_updated and source_updated_at and source_updated_at <= last_seen_updated:
                should_scrape = False
                logger.debug(f"Skipping unchanged dog {internal_id} ({animal_id})")
                continue

        if should_scrape:
            to_scrape[str_internal_id] = animal

    return to_scrape


def _scrape_animals_concurrent(to_scrape: Dict[str, Dict[str, Any]], creds: Dict[str, str], max_concurrent_scrapes: int) -> Dict[str, Dict[str, Any]]:
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
                    scraped = scraper.scrape_profile_only(animal_id)
                    end_time = time.time()
                    logger.info(f"Scraped {animal_id} in {end_time - start_time:.1f}s")
                    scraped_map[internal_id] = scraped
                except Exception as e:
                    logger.warning("Scrape failed for %s (%s): %s", animal_id, internal_id, e)
                    scraped_map[internal_id] = {"ScrapeError": str(e)}
        return scraped_map
    else:
        # Concurrent path using ThreadPoolExecutor
        def _scrape_chunk(items):
            """Scrape a chunk of animals using a dedicated scraper instance."""
            chunk_results = {}
            with ShelterLuvScraper(creds["username"], creds["password"]) as scraper:
                for internal_id, animal in items:
                    animal_id = animal.get("ID")
                    try:
                        logger.debug(f"Scraping {animal_id} ({internal_id}) in chunk...")
                        start_time = time.time()
                        scraped = scraper.scrape_profile_only(animal_id)
                        end_time = time.time()
                        logger.info(f"Scraped {animal_id} in {end_time - start_time:.1f}s")
                        chunk_results[internal_id] = scraped
                    except Exception as e:
                        logger.warning("Scrape failed for %s (%s): %s", animal_id, internal_id, e)
                        chunk_results[internal_id] = {"ScrapeError": str(e)}
            return chunk_results

        # Split work into chunks
        to_scrape_items = list(to_scrape.items())
        chunk_size = max(1, len(to_scrape_items) // max_concurrent_scrapes)
        chunks = [to_scrape_items[i:i + chunk_size] for i in range(0, len(to_scrape_items), chunk_size)]

        # Execute chunks concurrently
        scraped_map = {}

        with ThreadPoolExecutor(max_workers=max_concurrent_scrapes) as executor:
            chunk_futures = [executor.submit(_scrape_chunk, chunk) for chunk in chunks]
            for future in chunk_futures:
                chunk_results = future.result()
                scraped_map.update(chunk_results)

        return scraped_map

"""
ETL transform phase: Process and enrich raw data into validated dog records.
Pure functions that transform data without side effects.
"""

import time
from typing import Dict, Any, List, Literal
from dataclasses import dataclass
from scraper import ShelterLuvScraper
from enrichment import build_dog_record
from foster_mapping import build_foster_maps, build_event_maps
from errors import ScraperError, SchemaValidationError
from api.api_client_memos import get_animals_memos_batch


MemosMode = Literal["none", "api"]


@dataclass
class TransformConfig:
    """Configuration for the transform phase."""
    memos_mode: MemosMode
    max_concurrent_scrapes: int


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
    """
    import logging
    logger = logging.getLogger(__name__)

    if not extract_result.animals_by_id:
        return TransformResult(dogs=[], invalid_count=0, scraped_count=0, skipped_count=0)

    # Build mappings from events and people data
    foster_map = build_foster_maps(extract_result.events, extract_result.people)
    event_map = build_event_maps(extract_result.events)

    # Get memos if requested
    memos_data = _fetch_memos_if_needed(extract_result.animals_by_id, creds, config, logger)

    # Filter animals that need scraping (incremental logic)
    to_scrape = _filter_animals_to_scrape(extract_result)

    # Scrape additional data concurrently
    scraped_map = _scrape_animals_concurrent(to_scrape, creds, config.max_concurrent_scrapes)

    # Build dog records
    dogs, invalid_count = _build_dog_records(
        extract_result.animals_by_id, scraped_map, foster_map, event_map, memos_data, config
    )

    scraped_count = len(to_scrape)
    skipped_count = len(extract_result.animals_by_id) - len(to_scrape)

    logger.info(f"Processed {len(dogs)} dogs, {invalid_count} invalid, {scraped_count} scraped, {skipped_count} skipped")

    return TransformResult(
        dogs=dogs,
        invalid_count=invalid_count,
        scraped_count=scraped_count,
        skipped_count=skipped_count
    )


def _fetch_memos_if_needed(animals_by_id: Dict[str, Dict[str, Any]], creds: Dict[str, str],
                          config: TransformConfig, logger) -> Dict[str, str]:
    """Fetch memos data if API mode is enabled."""
    memos_data = {}
    if config.memos_mode == "api":
        try:
            logger.info(f"Fetching memos via API for {len(animals_by_id)} animals")
            memos_results = get_animals_memos_batch(creds["api_key"], list(animals_by_id.keys()))
            # Convert MemoResult dict to simple memos_html dict for backward compatibility
            memos_data = {internal_id: result.memos_html for internal_id, result in memos_results.items()}
        except Exception as e:
            logger.warning(f"Failed to fetch memos via API: {e}")
            # On API failure, use empty memos
            memos_data = {internal_id: "" for internal_id in animals_by_id.keys()}
    return memos_data


def _filter_animals_to_scrape(extract_result) -> Dict[str, Dict[str, Any]]:
    """Filter animals that need scraping based on incremental logic."""
    import logging
    logger = logging.getLogger(__name__)

    to_scrape = {}
    for internal_id, animal in extract_result.animals_by_id.items():
        animal_id = animal.get("ID")
        str_internal_id = str(internal_id)

        if not animal_id or not internal_id:
            continue

        # Check if we should skip this animal due to no changes
        should_scrape = True
        if extract_result.existing_metadata:
            meta = extract_result.existing_metadata.get(str_internal_id, {})
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


def _build_dog_records(animals_by_id: Dict[str, Dict[str, Any]], scraped_map: Dict[str, Dict[str, Any]],
                      foster_map: Dict[str, Dict[str, Any]], event_map: Dict[str, Dict[str, Any]],
                      memos_data: Dict[str, str], config: TransformConfig) -> tuple[List[Dict[str, Any]], int]:
    """Build validated dog records from all available data."""
    import logging
    logger = logging.getLogger(__name__)

    dogs = []
    invalid_count = 0

    for internal_id, animal in animals_by_id.items():
        if not internal_id:
            continue

        # Get scraped data (may be empty or have error)
        scraped_data = scraped_map.get(str(internal_id), {})

        # Get foster info
        foster_info = foster_map.get(str(internal_id), {})
        # Get event info
        event_info = event_map.get(str(internal_id), {})

        # Get memo HTML explicitly
        memo_html = ""
        if config.memos_mode == "api":
            memo_html = memos_data.get(str(internal_id), "")

        try:
            dog_record = build_dog_record(animal, scraped_data, foster_info, event_info, memo_html=memo_html)
            dogs.append(dog_record)
        except SchemaValidationError as e:
            logger.warning("Skipping invalid dog %s: %s", internal_id, e)
            invalid_count += 1

    return dogs, invalid_count


def _scrape_animals_concurrent(to_scrape: Dict[str, Dict[str, Any]], creds: Dict[str, str], max_concurrent_scrapes: int) -> Dict[str, Dict[str, Any]]:
    """Scrape animals concurrently using the specified concurrency level."""
    import logging
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
                except ScraperError as e:
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
                    except ScraperError as e:
                        logger.warning("Scrape failed for %s (%s): %s", animal_id, internal_id, e)
                        chunk_results[internal_id] = {"ScrapeError": str(e)}
            return chunk_results

        # Split work into chunks
        to_scrape_items = list(to_scrape.items())
        chunk_size = max(1, len(to_scrape_items) // max_concurrent_scrapes)
        chunks = [to_scrape_items[i:i + chunk_size] for i in range(0, len(to_scrape_items), chunk_size)]

        # Execute chunks concurrently
        from concurrent.futures import ThreadPoolExecutor
        scraped_map = {}

        with ThreadPoolExecutor(max_workers=max_concurrent_scrapes) as executor:
            chunk_futures = [executor.submit(_scrape_chunk, chunk) for chunk in chunks]
            for future in chunk_futures:
                chunk_results = future.result()
                scraped_map.update(chunk_results)

        return scraped_map

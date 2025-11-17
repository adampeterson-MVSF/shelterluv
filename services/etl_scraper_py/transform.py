"""
ETL transform phase: Process and enrich raw data into validated dog records.
Pure functions that transform data without side effects.
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Literal

from enrichment import build_dog_record
from errors import SchemaValidationError, ScraperError
from foster_mapping import build_event_maps, build_foster_maps

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

        # Get memo HTML from scraped data (summary page) or fallback to extracted memos
        memo_html = scraped_data.get("MemosRawHTML", memos_data.get(str(internal_id), ""))

        try:
            dog_record = build_dog_record(
                animal, scraped_data, foster_info, event_info, memo_html=memo_html
            )
            dogs.append(dog_record)
        except SchemaValidationError as e:
            logger.warning("Skipping invalid dog %s: %s", internal_id, e)
            invalid_count += 1

    return dogs, invalid_count

"""
ETL pipeline orchestration module.
Thin coordination layer that wires together extract, transform, and load phases.
"""

from typing import Dict, Any
from dataclasses import dataclass, asdict
from extract import extract, ExtractResult
from transform import transform, TransformConfig, TransformResult
from load import load, LoadResult
from config import EtlConfig
from secret_manager import get_shelterluv_creds
from common import get_logger

# Scraper version for tracking data changes and debugging
# Update this when scraper logic changes significantly
SCRAPER_VERSION = "1.0.0"

logger = get_logger(__name__)

@dataclass
class PipelineStats:
    """Structured dataclass for ETL pipeline statistics."""

    # Extract phase stats
    num_in_custody_ids: int = 0  # Number of IDs scraped from in-custody view
    num_animals_fetched_from_api: int = 0  # Number successfully fetched via API
    total_events_fetched: int = 0
    total_people_fetched: int = 0

    # Transform phase stats
    dogs_processed: int = 0
    dogs_invalid: int = 0
    dogs_scraped: int = 0  # Number of dogs that were scraped (vs skipped)
    dogs_skipped_unchanged: int = 0  # Number of dogs skipped due to no changes

    # Load phase stats
    dogs_written: int = 0
    dogs_deleted: int = 0

    # Derived data stats
    dogs_with_foster: int = 0

    # Error tracking
    events_fetch_failed: bool = False
    people_fetch_failed: bool = False
    partial_data: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility."""
        result = asdict(self)
        # Add backward compatibility aliases
        result["total_animals_fetched"] = result["num_animals_fetched_from_api"]
        return result

    def __str__(self) -> str:
        """String representation for logging."""
        return f"PipelineStats({self.dogs_processed} processed, {self.dogs_written} written, {self.dogs_deleted} deleted)"

def compute_stats(extract_result: ExtractResult, transform_result: TransformResult, load_result: LoadResult) -> PipelineStats:
    """Compute statistics from all ETL phases."""
    return PipelineStats(
        num_in_custody_ids=len(extract_result.in_custody_ids),
        num_animals_fetched_from_api=len(extract_result.animals_by_id),
        total_events_fetched=len(extract_result.events),
        total_people_fetched=len(extract_result.people),
        dogs_processed=len(transform_result.dogs),
        dogs_invalid=transform_result.invalid_count,
        dogs_scraped=transform_result.scraped_count,
        dogs_skipped_unchanged=transform_result.skipped_count,
        dogs_written=load_result.dogs_written,
        dogs_deleted=load_result.dogs_deleted,
        dogs_with_foster=sum(1 for d in transform_result.dogs if d.get("FosterName")),
        events_fetch_failed=extract_result.events_failed,
        people_fetch_failed=extract_result.people_failed,
        partial_data=extract_result.events_failed or extract_result.people_failed,
    )


def run_etl_process(config: EtlConfig, timing_hooks: Dict[str, callable] | None = None) -> Dict[str, Any]:
    """
    Orchestrates the ETL pipeline with logging and timing hooks.
    Thin coordination layer that wires together extract, transform, and load phases.
    """
    import time

    # Schema synchronization check (dev/test only)
    if not config.is_prod():
        try:
            from schema import assert_size_order_matches_schema
            assert_size_order_matches_schema()
        except Exception as e:
            logger.warning(f"Schema synchronization check failed: {e}")

    # Initialize timing hooks
    timing_hooks = timing_hooks or {}

    def hook(name: str):
        fn = timing_hooks.get(name)
        if fn:
            fn(name)

    logger.info(f"Starting ETL process with scraper version {SCRAPER_VERSION}")
    logger.info(f"Config: profile={config.env_profile.value}, memos_mode={config.memos_mode}, concurrency={config.max_concurrent_scrapes}, dry_run={config.dry_run}")

    # Get credentials using config
    creds = get_shelterluv_creds(config.secrets)

    # EXTRACT
    hook("extract_start")
    extract_result = extract(creds, config.animal_limit)
    hook("extract_end")

    # TRANSFORM & ENRICH
    hook("transform_start")
    transform_config = TransformConfig(memos_mode=config.memos_mode, max_concurrent_scrapes=config.max_concurrent_scrapes)
    transform_result = transform(extract_result, creds, transform_config)
    hook("transform_end")

    # LOAD
    hook("load_start")
    load_result = load(transform_result, config.dry_run)
    hook("load_end")

    # COMPUTE STATS
    stats = compute_stats(extract_result, transform_result, load_result)

    logger.info(f"ETL complete: {stats}")
    return stats.to_dict()


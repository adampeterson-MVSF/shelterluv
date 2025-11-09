"""
ETL load phase: Write dog records to Firestore and purge stale records.
Pure functions that handle database operations.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from transform import TransformResult
import db


@dataclass
class LoadResult:
    """Result of the load phase."""
    dogs_written: int
    dogs_deleted: int


def load(transform_result: TransformResult, dry_run: bool = False) -> LoadResult:
    """
    Load dog records to Firestore and purge stale records.
    This is a pure function that takes TransformResult and returns LoadResult.
    """
    import logging
    logger = logging.getLogger(__name__)

    if not transform_result.dogs:
        # Only purge stale records if no dogs to write
        deleted_count = db.purge_stale_dogs(set(), dry_run=dry_run) if not dry_run else 0
        return LoadResult(dogs_written=0, dogs_deleted=deleted_count)

    # Get active IDs from processed dogs
    active_ids = {dog["Internal-ID"] for dog in transform_result.dogs}

    # Write dogs to Firestore
    write_stats = db.write_dogs(transform_result.dogs, dry_run=dry_run)
    dogs_written = write_stats["dogs_written"]

    # Purge stale records
    dogs_deleted = db.purge_stale_dogs(active_ids, dry_run=dry_run)

    logger.info(f"Loaded {dogs_written} dogs, deleted {dogs_deleted} stale records")

    return LoadResult(dogs_written=dogs_written, dogs_deleted=dogs_deleted)

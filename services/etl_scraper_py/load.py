"""
ETL load phase: Write dog records to Firestore and purge stale records.
Pure functions that handle database operations.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

import db
from transform import TransformResult


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
    active_ids = {dog["internalId"] for dog in transform_result.dogs}

    # Write dogs and purge stale records in single operation
    load_stats = db.write_dogs_and_purge_stale(transform_result.dogs, active_ids, dry_run=dry_run)

    logger.info(
        f"Loaded {load_stats['dogs_written']} dogs, deleted {load_stats['dogs_deleted']} stale records"
    )

    return LoadResult(
        dogs_written=load_stats["dogs_written"], dogs_deleted=load_stats["dogs_deleted"]
    )

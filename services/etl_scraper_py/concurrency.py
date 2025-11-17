"""
Concurrency utilities for ETL pipeline.

Provides reusable functions for concurrent processing with proper error handling.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


def execute_concurrent_chunks[T](
    items: List[T],
    process_chunk_fn: Callable[[List[T]], Dict[str, Any]],
    max_workers: int,
    chunk_size: int = None
) -> Dict[str, Any]:
    """
    Execute processing of items in concurrent chunks using ThreadPoolExecutor.

    Args:
        items: List of items to process
        process_chunk_fn: Function that takes a chunk of items and returns a dict of results
        max_workers: Maximum number of concurrent workers
        chunk_size: Size of each chunk (auto-calculated if None)

    Returns:
        Combined results from all chunks
    """
    if not items:
        return {}

    # Auto-calculate chunk size if not provided
    if chunk_size is None:
        chunk_size = max(1, len(items) // max_workers)

    # Split items into chunks
    chunks = [
        items[i : i + chunk_size] for i in range(0, len(items), chunk_size)
    ]

    logger.info(f"Processing {len(items)} items in {len(chunks)} chunks with {max_workers} workers")

    # Execute chunks concurrently
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        chunk_futures = [executor.submit(process_chunk_fn, chunk) for chunk in chunks]

        for future in chunk_futures:
            try:
                chunk_results = future.result()
                results.update(chunk_results)
            except Exception as e:
                logger.error(f"Chunk processing failed: {e}")
                # Continue with other chunks rather than failing entirely

    logger.info(f"Completed concurrent processing: {len(results)} results")
    return results

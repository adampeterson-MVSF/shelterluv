#!/usr/bin/env python3
"""
Simple performance test for ETL pipeline.

⚠️  DEVELOPMENT ONLY - DO NOT USE IN PRODUCTION ⚠️

Usage:
    python pipeline_performance_test.py [--dogs N] [--dry-run]

Tests pipeline performance with specified number of dogs.
Outputs JSON results for CI integration.
"""

import argparse
import logging
import os
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Optional imports for memory tracking
try:
    import tracemalloc

    import psutil

    MEMORY_TRACKING_AVAILABLE = True
except ImportError:
    MEMORY_TRACKING_AVAILABLE = False

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from project_safety import ensure_dev_project
from config import EtlConfig
from secret_manager import get_shelterluv_creds

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance measurement results."""

    total_time: float
    extract_animals_time: float
    extract_events_time: float
    extract_people_time: float
    transform_mappings_time: float
    scrape_transform_time: float
    load_time: float
    memory_peak: int
    memory_current: int
    dogs_processed: int
    dogs_written: int
    dogs_deleted: int


@contextmanager
def timer(name: str, metrics_dict: Optional[Dict[str, float]] = None):
    """Context manager for timing code blocks with optional metrics storage."""
    start_time = time.perf_counter()
    logger.info(f"Starting: {name}")
    try:
        yield
    finally:
        duration = time.perf_counter() - start_time
        logger.info(".2f")
        if metrics_dict is not None:
            metrics_dict[name] = duration


@contextmanager
def memory_tracker(track_memory: bool = False):
    """Context manager for memory usage tracking."""
    memory_info = {"peak": 0, "current": 0}

    if track_memory and MEMORY_TRACKING_AVAILABLE:
        tracemalloc.start()
        process = psutil.Process()

        initial_memory = process.memory_info().rss
        logger.info(f"Initial memory usage: {initial_memory / 1024 / 1024:.2f} MB")

    try:
        yield memory_info
    finally:
        if track_memory and MEMORY_TRACKING_AVAILABLE:
            # Get peak memory usage during execution
            current, peak = tracemalloc.get_traced_memory()
            memory_info["peak"] = peak
            memory_info["current"] = current

            final_memory = process.memory_info().rss
            logger.info(".2f")
            logger.info(".2f")
            logger.info(".2f")

            tracemalloc.stop()
        elif track_memory and not MEMORY_TRACKING_AVAILABLE:
            logger.warning(
                "Memory tracking requested but psutil/tracemalloc not available. Install with: pip install psutil"
            )


def mock_firestore_operations():
    """Mock Firestore operations for dry-run testing."""
    import types

    # Create mock db module
    mock_db = types.ModuleType("db")
    mock_db.write_dogs = lambda dogs, dry_run=False: {
        "dogs_written": len(dogs) if not dry_run else 0,
        "batch_count": 1,
    }
    mock_db.purge_stale_dogs = lambda ids, dry_run=False: 0
    mock_db.get_db = lambda: None
    sys.modules["db"] = mock_db


def run_pipeline_performance_test(
    dog_limit: int,
    dry_run: bool = True,
    track_memory: bool = False,
    memos_mode: str = "none",
    max_concurrent_scrapes: int = 1,
) -> PerformanceMetrics:
    """
    Run a single performance test iteration with the specified dog limit.

    Args:
        dog_limit: Maximum number of dogs to process
        dry_run: If True, skip actual Firestore writes
        track_memory: If True, track memory usage
        memos_mode: Whether to scrape memos ("none" or "full")

    Returns:
        PerformanceMetrics object with timing and memory data
    """
    print(
        f"DEBUG: run_pipeline_performance_test called with dog_limit={dog_limit}, dry_run={dry_run}"
    )
    import pipeline

    # Create ETL config
    config = EtlConfig.from_env(
        overrides={
            "dry_run": dry_run,
            "animal_limit": dog_limit,
            "memos_mode": memos_mode,
            "max_concurrent_scrapes": max_concurrent_scrapes,
        }
    )

    # Get credentials
    creds = get_shelterluv_creds(config.secrets)

    # Timing storage for pipeline hooks
    stage_timings = {
        "extract_events_start": None,
        "extract_events_end": None,
        "extract_people_start": None,
        "extract_people_end": None,
        "transform_mappings_start": None,
        "transform_mappings_end": None,
        "scrape_transform_start": None,
        "scrape_transform_end": None,
        "load_start": None,
        "load_end": None,
    }

    # Timing hook functions
    def record_timing(hook_name: str):
        stage_timings[hook_name] = time.perf_counter()

    timing_hooks = {name: lambda name=name: record_timing(name) for name in stage_timings.keys()}

    timings = {}
    memory_info = {"peak": 0, "current": 0}

    with memory_tracker(track_memory) as memory_info:
        with timer("Total Pipeline Execution", timings):
            # Initialize Firestore (will be mocked if dry_run=True)
            if dry_run:
                mock_firestore_operations()

        # For performance testing, skip heavy operations that cause rate limiting
        # We'll mock the events and people APIs to avoid fetching thousands of records
        import unittest.mock

        with unittest.mock.patch(
            "api_client.get_animal_events"
        ) as mock_events, unittest.mock.patch("api_client.get_people") as mock_people:

            # Return minimal mock data to avoid rate limiting
            mock_events.return_value = []
            mock_people.return_value = []

            # Run the ETL process with timing hooks
            stats = pipeline.run_etl_process(config, creds, timing_hooks)

    # Calculate stage durations
    extract_events_time = (
        (stage_timings["extract_events_end"] - stage_timings["extract_events_start"])
        if stage_timings["extract_events_end"] and stage_timings["extract_events_start"]
        else 0
    )
    extract_people_time = (
        (stage_timings["extract_people_end"] - stage_timings["extract_people_start"])
        if stage_timings["extract_people_end"] and stage_timings["extract_people_start"]
        else 0
    )
    transform_mappings_time = (
        (stage_timings["transform_mappings_end"] - stage_timings["transform_mappings_start"])
        if stage_timings["transform_mappings_end"] and stage_timings["transform_mappings_start"]
        else 0
    )
    scrape_transform_time = (
        (stage_timings["scrape_transform_end"] - stage_timings["scrape_transform_start"])
        if stage_timings["scrape_transform_end"] and stage_timings["scrape_transform_start"]
        else 0
    )
    load_time = (
        (stage_timings["load_end"] - stage_timings["load_start"])
        if stage_timings["load_end"] and stage_timings["load_start"]
        else 0
    )

    # Extract metrics
    metrics = PerformanceMetrics(
        total_time=timings.get("Total Pipeline Execution", 0),
        extract_animals_time=0,  # Not currently timed separately
        extract_events_time=extract_events_time,
        extract_people_time=extract_people_time,
        transform_mappings_time=transform_mappings_time,
        scrape_transform_time=scrape_transform_time,
        load_time=load_time,
        memory_peak=memory_info["peak"],
        memory_current=memory_info["current"],
        dogs_processed=stats.get("dogs_processed", 0),
        dogs_written=stats.get("dogs_written", 0),
        dogs_deleted=stats.get("dogs_deleted", 0),
    )

    return metrics


def print_performance_report(
    metrics_list: List[PerformanceMetrics], dog_limits: List[int], iterations: int
):
    """Print a detailed performance report."""
    print("\n" + "=" * 80)
    print("PIPELINE PERFORMANCE TEST RESULTS")
    print("=" * 80)

    for i, dog_limit in enumerate(dog_limits):
        print(f"\n--- Testing with {dog_limit} dogs ---")

        # Get metrics for this dog limit (find metrics where dogs_processed matches or is close to limit)
        limit_metrics = [
            m
            for m in metrics_list
            if abs(m.dogs_processed - dog_limit) <= 2 or m.dogs_processed <= dog_limit
        ]

        if not limit_metrics:
            print("No data collected for this limit")
            continue

        # Calculate averages
        avg_total_time = sum(m.total_time for m in limit_metrics) / len(limit_metrics)
        avg_memory_peak = sum(m.memory_peak for m in limit_metrics) / len(limit_metrics)

        print(".2f")
        if avg_memory_peak > 0:
            print(".2f")

        # Stage timing breakdown
        avg_extract_events = sum(m.extract_events_time for m in limit_metrics) / len(limit_metrics)
        avg_extract_people = sum(m.extract_people_time for m in limit_metrics) / len(limit_metrics)
        avg_transform_mappings = sum(m.transform_mappings_time for m in limit_metrics) / len(
            limit_metrics
        )
        avg_scrape_transform = sum(m.scrape_transform_time for m in limit_metrics) / len(
            limit_metrics
        )
        avg_load = sum(m.load_time for m in limit_metrics) / len(limit_metrics)

        print("\nStage Timing Breakdown:")
        print(".2f")
        print(".2f")
        print(".2f")
        print(".2f")
        print(".2f")

        print(f"\nData Processing:")
        print(
            f"Average dogs processed: {sum(m.dogs_processed for m in limit_metrics) / len(limit_metrics):.1f}"
        )
        print(
            f"Average dogs written: {sum(m.dogs_written for m in limit_metrics) / len(limit_metrics):.1f}"
        )
        print(
            f"Average dogs deleted: {sum(m.dogs_deleted for m in limit_metrics) / len(limit_metrics):.1f}"
        )

        if len(limit_metrics) > 1:
            times = [m.total_time for m in limit_metrics]
            print(".2f")
            print(".2f")

        # Per-dog performance
        actual_dogs = sum(m.dogs_processed for m in limit_metrics) / len(limit_metrics)
        if actual_dogs > 0:
            avg_time_per_dog = avg_total_time / actual_dogs
            print(".3f")

            # Bottleneck analysis
            print("\nBottleneck Analysis:")
            stages = [
                ("Extract Events", avg_extract_events),
                ("Extract People", avg_extract_people),
                ("Transform Mappings", avg_transform_mappings),
                ("Scrape & Transform", avg_scrape_transform),
                ("Load", avg_load),
            ]
            slowest_stage = max(stages, key=lambda x: x[1])
            print(".2f")


def main():
    """Simple performance test - single scenario, JSON output."""
    parser = argparse.ArgumentParser(description="Simple ETL pipeline performance test")
    parser.add_argument(
        "--dogs", type=int, default=5, help="Number of dogs to test with (default: 5)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", default=True, help="Run in dry-run mode (default: True)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", default=False, help="Enable verbose debug output"
    )

    args = parser.parse_args()

    # Set up verbose logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    # Load environment variables from .env files (after verbose flag is parsed)
    if args.verbose:
        print("DEBUG: Loading environment variables...")
    try:
        from dotenv import load_dotenv

        if args.verbose:
            print("DEBUG: Loading .env")
        load_dotenv(".env")
        if args.verbose:
            print("DEBUG: Loading .env.local")
        load_dotenv(".env.local")
        if args.verbose:
            print("DEBUG: Environment variables loaded")
    except ImportError:
        # dotenv not available, continue with existing env vars
        if args.verbose:
            print("DEBUG: python-dotenv not available")
        pass

    if args.verbose:
        print(f"DEBUG: GOOGLE_CLOUD_PROJECT = {os.environ.get('GOOGLE_CLOUD_PROJECT')}")
        print(f"DEBUG: SHELTERLUV_USER = {os.environ.get('SHELTERLUV_USER', 'NOT SET')}")
        print(
            f"DEBUG: SHELTERLUV_API_KEY = {'SET' if os.environ.get('SHELTERLUV_API_KEY') else 'NOT SET'}"
        )

    # Safety check - require DEV_SCRIPTS_ENABLED for destructive operations
    if not args.dry_run and os.environ.get("DEV_SCRIPTS_ENABLED") != "1":
        print("❌ DEV_SCRIPTS_ENABLED=1 required for non-dry-run performance tests")
        return 1

    print(f"Running performance test with {args.dogs} dogs (dry-run: {args.dry_run})...")

    try:
        start_time = time.time()
        metrics = run_pipeline_performance_test(
            dog_limit=args.dogs,
            dry_run=args.dry_run,
            track_memory=False,
            memos_mode="api",
            max_concurrent_scrapes=2,
        )
        end_time = time.time()

        # Add total time to metrics
        result = metrics.to_dict()
        result["total_time"] = end_time - start_time

        # Output JSON for CI integration
        import json

        print(json.dumps(result, indent=2))

        return 0

    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

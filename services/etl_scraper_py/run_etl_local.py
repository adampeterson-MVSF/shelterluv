#!/usr/bin/env python3
"""
Local ETL runner for testing and development.
Runs the full ETL pipeline without requiring Cloud Functions Framework.

This is the main CLI interface for running ETL during local development.
For diagnostic tools, see run_pipeline.py or run_single_dog_pipeline.py.

Usage:
    python run_etl_local.py                    # Full ETL run
    python run_etl_local.py --dry-run          # Preview what would be written
    python run_etl_local.py --limit 5          # Test with only 5 animals
    python run_etl_local.py --limit 10 --dry-run  # Preview with 10 animals
"""

import argparse
import logging
import os
from pathlib import Path

import pipeline
from logging_config import get_logger, setup_logging

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)
from config import EtlConfig, assert_dev_safe_config, load_dotenv_files
from errors import EtlError
from secret_manager import get_shelterluv_creds

# Configure logging
setup_logging()
logger = get_logger(__name__)


def main():
    """Run the ETL process locally."""
    # Load .env and .env.local files
    load_dotenv_files()
    parser = argparse.ArgumentParser(
        description="Run ETL pipeline locally for testing and development",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_etl_local.py                               # Full ETL run (fast, no memos)
  python run_etl_local.py --dry-run                     # Preview what would be written
  python run_etl_local.py --limit 5                     # Test with only 5 animals (fast)
  python run_etl_local.py --limit 3 --memos-mode api     # Test with memos (slower)
  python run_etl_local.py --limit 10 --dry-run          # Preview with 10 animals
        """,
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run in dry-run mode (no writes to Firestore)"
    )
    parser.add_argument(
        "--limit", type=int, metavar="N", help="Limit processing to first N animals (for testing)"
    )
    parser.add_argument(
        "--memos-mode",
        choices=["none", "api"],
        help="Override memo fetching mode: none (fast, no memos) or api (slow, fetch memos)",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        metavar="N",
        help="Override maximum concurrent API requests (reduce for rate limiting)",
    )
    parser.add_argument(
        "--env-profile",
        choices=["dev", "staging", "e2e", "demo", "prod"],
        help="Override environment profile",
    )

    args = parser.parse_args()

    # Create configuration with CLI overrides
    config_overrides = {}
    if args.dry_run:
        config_overrides["dry_run"] = True
    if args.limit:
        config_overrides["animal_limit"] = args.limit
    if args.memos_mode:
        config_overrides["memos_mode"] = args.memos_mode
    if args.max_concurrent:
        config_overrides["max_concurrent_scrapes"] = args.max_concurrent
    if args.env_profile:
        config_overrides["env_profile"] = args.env_profile

    config = EtlConfig.from_env(overrides=config_overrides)

    # Safety check for development environment
    assert_dev_safe_config(config, "local ETL run")

    # Get credentials using config
    creds = get_shelterluv_creds(config.secrets)

    logger.info("=" * 80)
    if config.dry_run:
        logger.info("Starting local ETL process (DRY RUN MODE)...")
    else:
        logger.info("Starting local ETL process...")
    if config.animal_limit:
        logger.info(f"Limited to {config.animal_limit} animals for testing")
    logger.info(
        f"Config: profile={config.env_profile.value}, project={config.project_id}, memos={config.memos_mode}"
    )
    logger.info("=" * 80)

    try:
        stats = pipeline.run_etl_process(config, creds)

        logger.info("=" * 80)
        if args.dry_run:
            logger.info("DRY RUN COMPLETED SUCCESSFULLY!")
            logger.info("(No data was written to Firestore)")
        else:
            logger.info("ETL COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        logger.info(f"In-custody IDs scraped: {stats['num_in_custody_ids']}")
        logger.info(f"Animals fetched from API: {stats['num_animals_fetched_from_api']}")
        logger.info(f"Total events fetched: {stats['total_events_fetched']}")
        logger.info(f"Total people fetched: {stats['total_people_fetched']}")
        logger.info(f"Dogs processed: {stats['dogs_processed']}")
        logger.info(f"Dogs with foster info: {stats['dogs_with_foster']}")
        logger.info(f"Dogs written to Firestore: {stats['dogs_written']}")
        logger.info(f"Dogs deleted (stale): {stats['dogs_deleted']}")
        logger.info(f"Invalid dogs (skipped): {stats['dogs_invalid']}")
        logger.info("=" * 80)

        return 0

    except EtlError as e:
        logger.error("=" * 80)
        if args.dry_run:
            logger.error(f"DRY RUN ETL FAILED: {e}")
        else:
            logger.error(f"ETL FAILED: {e}")
        logger.error("=" * 80)
        return 1

    except Exception as e:
        logger.exception("=" * 80)
        if args.dry_run:
            logger.exception(f"DRY RUN UNEXPECTED ERROR: {e}")
        else:
            logger.exception(f"UNEXPECTED ERROR: {e}")
        logger.exception("=" * 80)
        return 1


if __name__ == "__main__":
    exit(main())

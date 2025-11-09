#!/usr/bin/env python3
"""
Debug tool for ShelterLuv in-custody ID scraping.

This diagnostic script scrapes only the in-custody animal IDs from ShelterLuv UI
without processing the full animal records. Useful for debugging ShelterLuv UI changes.

Usage:
    python debug_in_custody_scraping.py
"""

import logging
from ..scraper.in_custody_ids import scrape_in_custody_ids
from ..secret_manager import get_shelterluv_creds
from ..common import guard_dev_only

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Debug ShelterLuv in-custody ID scraping."""
    # Safety check for development environment
    guard_dev_only()

    logger.info("=" * 80)
    logger.info("DEBUG: In-Custody ID Scraping Only")
    logger.info("This will scrape IDs from ShelterLuv UI without processing animals")
    logger.info("=" * 80)

    try:
        creds = get_shelterluv_creds()
        ids = scrape_in_custody_ids(creds["username"], creds["password"])

        logger.info(f"Found {len(ids)} animals currently in custody")
        if ids:
            logger.info("First few IDs: " + ", ".join(sorted(list(ids))[:5]))
            if len(ids) > 5:
                logger.info(f"... and {len(ids) - 5} more")
        else:
            logger.warning("No animals found in custody")

        return 0

    except Exception as e:
        logger.error(f"In-custody ID scraping failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

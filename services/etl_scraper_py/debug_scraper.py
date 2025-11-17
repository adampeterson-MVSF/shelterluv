#!/usr/bin/env python3
"""
Debug script to test ShelterLuv scraping functionality.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scraper.in_custody_ids import scrape_in_custody_ids
from secret_manager import get_shelterluv_creds
from config import EtlConfig

def main():
    print("🔍 Testing ShelterLuv scraper...")

    # Load config
    config = EtlConfig.from_env()

    # Get credentials
    creds = get_shelterluv_creds(config.secrets)
    print(f"✅ Got credentials for user: {creds.username}")

    print("🌐 Attempting to scrape in-custody IDs...")
    try:
        ids = scrape_in_custody_ids(creds.username, creds.password)
        print(f"✅ Found {len(ids)} animals in custody: {sorted(ids)[:5]}..." if len(ids) <= 5 else f"✅ Found {len(ids)} animals in custody: {sorted(list(ids)[:5])}...")

        if len(ids) == 0:
            print("❌ ERROR: No animals found! This indicates a scraping failure.")
            return 1

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())

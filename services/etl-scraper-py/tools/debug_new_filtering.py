#!/usr/bin/env python3
"""
MANUAL TOOL - do not add to CI/test suite.

Debug script to verify the new filtering logic works correctly.
This script hits the live ShelterLuv API and should only be run manually for diagnostics.
"""

import sys
import os
from collections import Counter
from dotenv import load_dotenv

# Load environment variables from .env files
load_dotenv('.env')
load_dotenv('.env.local')

# Add the ETL service path to import modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ..api import get_all_animals_in_custody, BASE_URL
from ..secret_manager import get_shelterluv_creds

def debug_new_filtering():
    """Debug the new filtering logic."""

    try:
        # Get credentials from secret manager (never hardcoded!)
        creds = get_shelterluv_creds()
        api_key = creds["api_key"]

        print("🔍 DEBUGGING NEW FILTERING LOGIC:")
        print("Should only include statuses starting with 'Headquarters' or 'Foster'")
        print()

        # First, let's see what statuses are actually available in the API
        print("First, checking what statuses exist in the API...")
        import requests

        headers = {"Authorization": f"Bearer {api_key}"}
        params = {"limit": 100}

        all_api_animals = []
        url = f"{BASE_URL}/animals"

        page_count = 0
        while url:
            page_count += 1
            response = requests.get(url, headers=headers, params=params, timeout=(3, 10))
            response.raise_for_status()
            data = response.json()
            animals_page = data.get("animals", [])
            all_api_animals.extend(animals_page)
            url = data.get("next_page")
            params = {}

            print(f"Page {page_count}: {len(animals_page)} animals (total: {len(all_api_animals)})")

            # Safety limit to avoid infinite loops
            if len(all_api_animals) >= 2000:
                print("Hit 2000-animal safety limit")
                break

        print(f"\nTotal animals in API: {len(all_api_animals)}")

        # Check all statuses
        all_statuses = []
        for animal in all_api_animals:
            status = animal.get("Status", "")
            all_statuses.append(status)

        all_status_counts = Counter(all_statuses)
        print("\nALL STATUSES IN API:")
        print("=" * 60)
        for status, count in sorted(all_status_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {status}: {count}")

        # Now test our filtering
        print("\n" + "="*80)
        print("TESTING NEW FILTERING LOGIC:")
        print("="*80)

        # Get animals using new filtering
        animals = get_all_animals_in_custody(api_key)

        print(f"Found {len(animals)} animals in custody with new filtering")
        print()

        # Analyze the statuses
        statuses = []
        for animal in animals:
            status = animal.get("Status", "")
            statuses.append(status)

        status_counts = Counter(statuses)

        print("STATUSES OF ANIMALS INCLUDED BY NEW LOGIC:")
        print("=" * 60)
        for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {status}: {count}")

        print()
        print("SAMPLE ANIMALS (first 5):")
        print("=" * 60)
        for i, animal in enumerate(animals[:5]):
            internal_id = animal.get("Internal-ID", "N/A")
            name = animal.get("Name", "N/A")
            status = animal.get("Status", "N/A")
            print("2d: ID={} Name='{}' Status='{}'".format(
                i+1, internal_id, name, status
            ))

        print()
        print("VERIFICATION:")
        print("=" * 60)
        invalid_statuses = []
        for animal in animals:
            status = animal.get("Status", "")
            if not (status.startswith("Headquarters") or status.startswith("Foster")):
                invalid_statuses.append(status)

        if invalid_statuses:
            print(f"❌ ERROR: Found {len(invalid_statuses)} animals with invalid statuses:")
            for status in invalid_statuses[:5]:  # Show first 5
                print(f"  - {status}")
        else:
            print("✅ SUCCESS: All animals have valid in-custody statuses")

        print()
        print("This should now return only the dogs that are actually at Muttville!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_new_filtering()

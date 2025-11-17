#!/usr/bin/env python3
"""
MANUAL TOOL - do not add to CI/test suite.

Diagnostic script to examine ShelterLuv API responses and identify correct in-custody dog statuses.
This script fetches animals from the API and analyzes their statuses without any filtering.
"""

import json
import os
import sys
from collections import Counter

from dotenv import load_dotenv

# Load environment variables from .env files
load_dotenv(".env")
load_dotenv(".env.local")

# Add project root (which contains 'common')
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
# Add ETL service path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from api import BASE_URL, get_all_animals_in_custody
from schema import DOG_SCHEMA, _normalize_status, get_normalized_statuses
from secret_manager import get_shelterluv_creds


def analyze_statuses_from_user_input():
    """Analyze the statuses mentioned by the user to understand the filtering issue."""

    # Statuses that the user mentioned are being processed but are not in-custody dogs
    user_reported_pending_statuses = [
        "Headquarters Unavailable - Pending Medical Exam",
        "Headquarters Available (not online)",
        "Headquarters Unavailable - Pending Medical Results",
        "Headquarters Unavailable - Pending Behavioral Assessment",
        "Headquarters- Pending Adoption",
        "Headquarters Hospice Available (not online)",
        "Headquarters Available, Pending Partner",
        "Headquarters Available",
        "Headquarters Hospice Available",
        "Foster Unavailable - Pending Medical Exam",
        "Foster Available (not online)",
        "Foster Unavailable - Pending Medical Results",
        "Foster Unavailable- Pending Behavioral Assessment",
        "Foster- Pending Adoption",
        "Foster Hospice Available (not online)",
        "Foster Available, Pending Partner",
        "Foster Available",
        "Foster Hospice Available",
    ]

    print("ANALYSIS OF USER-REPORTED STATUSES:")
    print("=" * 60)
    print("User reported that these statuses are being processed but are NOT in-custody dogs:")
    print()

    included_count = 0
    excluded_count = 0

    for status in user_reported_pending_statuses:
        normalized = _normalize_status(status)
        if normalized in ("AVAILABLE", "PENDING", "HOLD", "UNKNOWN"):
            print("30")
            included_count += 1
        else:
            print("30")
            excluded_count += 1

    print()
    print(
        f"Summary: {included_count} statuses would be INCLUDED, {excluded_count} would be EXCLUDED"
    )
    print()

    print("CURRENT STATUS NORMALIZATION LOGIC:")
    print("=" * 60)
    print("- 'available' in status.lower() → AVAILABLE")
    print("- 'pending' in status.lower() → PENDING")
    print("- 'hold' in status.lower() → HOLD")
    print("- 'adopted' or 'serviced out' or 'transferred' or 'healthy in home' → ADOPTED")
    print("- Everything else → UNKNOWN")
    print()

    print("CURRENT API FILTERING:")
    print("- Only includes: AVAILABLE, PENDING, HOLD, UNKNOWN")
    print("- Excludes: ADOPTED")
    print()

    print("PROBLEM IDENTIFIED:")
    print("=" * 60)
    print("The user says ALL dogs from the pipeline are 'Pending Acceptance' and are NOT")
    print("actually in custody at Muttville. But the current logic maps all 'pending'")
    print("statuses to PENDING, which gets included in the 'in custody' filter.")
    print()
    print("This means the API is returning dogs that are pending acceptance/adoption")
    print("rather than dogs that are actually physically at the shelter.")
    print()

    print("QUESTIONS TO ANSWER:")
    print("=" * 60)
    print("1. What statuses represent dogs that are ACTUALLY in custody at Muttville?")
    print("2. Are there location-based indicators (Headquarters vs Foster vs Offsite)?")
    print("3. Is there a specific status pattern that indicates 'currently at shelter'?")
    print()

    # Suggest what the correct statuses might be
    print("POSSIBLE SOLUTION:")
    print("=" * 60)
    print("Based on the user's description, the correct in-custody statuses might be:")
    print("- Any status containing 'Available' (not 'Pending' or 'Unavailable')")
    print("- Location-based filtering (only 'Headquarters' or 'Foster' locations)")
    print("- Exclude any status with 'Pending' in it")
    print()
    print("But we need to test the API to see what statuses actually represent")
    print("dogs that are physically present at Muttville.")


def analyze_api_statuses():
    """Analyze the ShelterLuv API to see what statuses are actually returned."""

    # First show the analysis based on user's input
    analyze_statuses_from_user_input()

    print()
    print("=" * 80)
    print("ANALYZING SHELTERLUV API DIRECTLY:")
    print("=" * 80)

    # Get credentials from secret manager (never hardcoded!)
    creds = get_shelterluv_creds()
    api_key = creds["api_key"]

    print("Using secret manager credentials to analyze ShelterLuv API...")
    print("API key: [REDACTED]")

    # Make a direct API call to get all animals (bypass the current filtering)
    import requests

    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"limit": 100}  # Get first 100 for analysis

    all_animals = []
    url = f"{BASE_URL}/animals"

    print(f"API URL: {url}")
    print("Fetching animals from API...")

    try:
        while url and len(all_animals) < 1000:  # Safety limit
            response = requests.get(url, headers=headers, params=params, timeout=(3, 10))
            response.raise_for_status()

            data = response.json()
            animals = data.get("animals", [])

            all_animals.extend(animals)

            # Get the next page URL
            url = data.get("next_page")
            params = {}  # Clear params after first request

            print(f"Fetched {len(animals)} animals (total: {len(all_animals)})")

            # Safety limit for testing
            if len(all_animals) >= 500:
                print("Hit 500-animal limit for analysis")
                break

        print(f"\nTotal animals analyzed: {len(all_animals)}")
        print()

        # Analyze statuses
        raw_statuses = []
        normalized_statuses = []
        locations = []

        for animal in all_animals:
            raw_status = animal.get("Status", "")
            normalized = _normalize_status(raw_status)
            location = animal.get("Location", "")

            raw_statuses.append(raw_status)
            normalized_statuses.append(normalized)
            locations.append(location)

        # Count raw statuses
        raw_counts = Counter(raw_statuses)
        normalized_counts = Counter(normalized_statuses)
        location_counts = Counter(locations)

        print("RAW STATUSES (from ShelterLuv API):")
        print("=" * 60)
        for status, count in sorted(raw_counts.items(), key=lambda x: x[1], reverse=True):
            normalized = _normalize_status(status)
            print("25")

        print()
        print("NORMALIZED STATUSES (current mapping):")
        print("=" * 60)
        for status, count in sorted(normalized_counts.items(), key=lambda x: x[1], reverse=True):
            print("25")

        print()
        print("LOCATIONS:")
        print("=" * 60)
        for location, count in sorted(location_counts.items(), key=lambda x: x[1], reverse=True):
            print("25")

        print()
        print("CURRENT FILTERING ANALYSIS:")
        print("=" * 60)
        print("Current logic includes: AVAILABLE, PENDING, HOLD, UNKNOWN")
        print("Current logic excludes: ADOPTED")
        print()

        # Show what would be included vs excluded by current logic
        included_animals = []
        excluded_animals = []

        for animal in all_animals:
            raw_status = animal.get("Status", "")
            normalized = _normalize_status(raw_status)
            if normalized in ("AVAILABLE", "PENDING", "HOLD", "UNKNOWN"):
                included_animals.append(animal)
            else:
                excluded_animals.append(animal)

        print(
            f"By current logic: {len(included_animals)} would be INCLUDED, {len(excluded_animals)} would be EXCLUDED"
        )
        print()

        print("RAW API RESPONSE STRUCTURE (first animal - ALL fields):")
        print("=" * 60)
        if all_animals:
            animal = all_animals[0]
            print("ALL FIELDS in first animal:")
            for key, value in animal.items():
                print(f"  {key}: {value}")
            print()
        print()

        print("CHECKING FIELD VALUES FOR FIRST FEW ANIMALS:")
        print("=" * 60)
        if all_animals:
            for i, animal in enumerate(all_animals[:5]):
                print(f"Animal {i+1}:")
                print(f"  Status field: {repr(animal.get('Status'))}")
                print(f"  Name field: {repr(animal.get('Name'))}")
                print(f"  CurrentLocation: {repr(animal.get('CurrentLocation'))}")
                print(f"  InFoster: {repr(animal.get('InFoster'))}")
                print()

        print("SAMPLE OF ALL ANIMALS (first 10):")
        print("=" * 60)
        for i, animal in enumerate(all_animals[:10]):
            internal_id = animal.get("Internal-ID", "N/A")
            name = animal.get("Name", "N/A")
            status = animal.get("Status", "N/A")
            current_location = animal.get("CurrentLocation", "N/A")
            normalized = _normalize_status(status)

            print(
                "{:2d}: ID={} Name='{}' Status='{}' (normalized={}) CurrentLocation={}".format(
                    i + 1, internal_id, name, status, normalized, current_location
                )
            )

        print()
        print("WHICH STATUSES ARE INCLUDED BY CURRENT LOGIC?")
        print("=" * 60)
        included_statuses = set()
        for animal in included_animals:
            status = animal.get("Status", "")
            included_statuses.add(status)

        print("Unique statuses that get INCLUDED:")
        for status in sorted(included_statuses):
            count = sum(1 for a in included_animals if a.get("Status") == status)
            normalized = _normalize_status(status)
            print("20")

        excluded_statuses = set()
        for animal in excluded_animals:
            status = animal.get("Status", "")
            excluded_statuses.add(status)

        print()
        print("Unique statuses that get EXCLUDED:")
        for status in sorted(excluded_statuses):
            count = sum(1 for a in excluded_animals if a.get("Status") == status)
            normalized = _normalize_status(status)
            print("20")

        print()
        print("RECOMMENDATION:")
        print("=" * 60)
        print("Look at the 'RAW STATUSES' above. Which of these represent dogs that are")
        print("ACTUALLY in custody at Muttville right now? The user said the current")
        print("results are all 'Pending Acceptance' dogs that are not in custody.")
        print()
        print("We need to update the filtering logic to only include the correct statuses.")

    except Exception as e:
        print(f"Error analyzing API: {e}")
        import traceback

        traceback.print_exc()


def test_schema_ui_status_synchronization():
    """Test that schema statuses are properly defined."""
    print("TESTING SCHEMA STATUS VALIDITY:")
    print("=" * 60)

    # Get statuses from schema
    schema_statuses = set(get_normalized_statuses())
    print(f"Schema normalized statuses: {sorted(schema_statuses)}")

    # Verify schema contains the expected statuses
    expected_statuses = {"AVAILABLE", "ADOPTED", "PENDING", "HOLD", "UNKNOWN"}
    if schema_statuses == expected_statuses:
        print("✅ Schema contains expected status values")
        return True
    else:
        missing = expected_statuses - schema_statuses
        extra = schema_statuses - expected_statuses
        print("❌ Schema status mismatch:")
        if missing:
            print(f"  Missing statuses: {sorted(missing)}")
        if extra:
            print(f"  Extra statuses: {sorted(extra)}")
        print("Fix: Update dog.schema.json to match expected status values")
        return False


if __name__ == "__main__":
    # Run the API status analysis
    analyze_api_statuses()

    print()
    print("=" * 80)
    print()

    # Run the synchronization test
    success = test_schema_ui_status_synchronization()

    # Exit with error if synchronization failed
    if not success:
        sys.exit(1)

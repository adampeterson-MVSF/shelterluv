#!/usr/bin/env python3
"""
Test the new custody detection logic.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env files
load_dotenv('.env')
load_dotenv('.env.local')

# Add the ETL service path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'services', 'etl-scraper-py'))

from enrichment import _compute_is_in_custody

def test_custody_logic():
    """Test the new custody detection logic."""

    print("Testing custody detection logic...")
    print()

    # Test cases
    test_cases = [
        # API status, scraped data, expected result, description
        ("Pending Acceptance", {}, False, "Pending Acceptance without scraped data"),
        ("Transferred Out", {"FullAnimalProfile": "Headquarters Available (not online)"}, True, "Transferred Out but Headquarters Available in profile"),
        ("Healthy In Home", {"FullAnimalProfile": "Foster Unavailable - Pending Medical Exam"}, True, "Healthy In Home but Foster status in profile"),
        ("Pending Acceptance", {"FullAnimalProfile": "Headquarters Unavailable - Pending Medical Exam"}, True, "Pending Acceptance with Headquarters status"),
        ("Transferred Out", {"FullAnimalProfile": "Adopted by another organization"}, False, "Transferred Out with no custody indicators"),
        ("ADOPTED", {"FullAnimalProfile": "Headquarters Available"}, False, "ADOPTED status should never be in custody"),
    ]

    passed = 0
    total = len(test_cases)

    for api_status, dog_data, expected, description in test_cases:
        result = _compute_is_in_custody(api_status, dog_data)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status}: {description}")
        print(f"   API Status: '{api_status}', Expected: {expected}, Got: {result}")
        if result == expected:
            passed += 1
        print()

    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All custody detection tests passed!")
    else:
        print("⚠️  Some tests failed - review the logic")

if __name__ == "__main__":
    test_custody_logic()

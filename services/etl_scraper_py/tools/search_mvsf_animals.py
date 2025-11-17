#!/usr/bin/env python3
"""
Search for MVSF animals in ShelterLuv API.
"""

import os
import sys
from typing import Any, Dict, List

from api import get_all_animals_in_custody
from project_safety import guard_dev_only
from errors import ApiError
from secret_manager import get_shelterluv_creds


def search_mvsf_animals(api_key: str) -> List[Dict[str, Any]]:
    """Search for animals with MVSF in their ID."""
    try:
        # Get all animals in custody via the centralized API client
        all_animals = get_all_animals_in_custody(api_key)

        # Filter for MVSF animals
        mvsf_animals = [animal for animal in all_animals if "MVSF" in animal.get("ID", "")]

        return mvsf_animals[:10]  # Limit to first 10 to avoid too much data

    except ApiError as e:
        raise RuntimeError(f"Failed to search MVSF animals: {e}")


def main():
    # Safety check for development environment
    guard_dev_only()

    try:
        creds = get_shelterluv_creds()
        api_key = creds["api_key"]
    except Exception as e:
        print(f"Failed to get ShelterLuv credentials: {e}", file=sys.stderr)
        return 1

    try:
        animals = search_mvsf_animals(api_key)
        if animals:
            print(f"Found {len(animals)} MVSF animals:")
            for animal in animals[:5]:  # Show first 5
                print(
                    f"  ID: {animal.get('ID')}, Internal-ID: {animal.get('Internal-ID')}, Name: {animal.get('Name')}, Status: {animal.get('Status')}"
                )
            return 0
        else:
            print("No MVSF animals found", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Failed to search MVSF animals: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
⚠️  DEV-ONLY DIAGNOSTIC TOOL: Find Animal by ID ⚠️

Find a specific animal from ShelterLuv API by ID.
ONLY USE IN DEVELOPMENT/TESTING ENVIRONMENTS.
"""

import os
import sys
from typing import Any, Dict, Optional

from api import get_all_animals_in_custody
from project_safety import guard_dev_only
from errors import ApiError
from secret_manager import get_shelterluv_creds


def find_animal_by_id(api_key: str, animal_id: str) -> Optional[Dict[str, Any]]:
    """Find specific animal from ShelterLuv API by ID."""
    try:
        # Get all animals in custody via the centralized API client
        all_animals = get_all_animals_in_custody(api_key)

        # Find the specific animal
        for animal in all_animals:
            if animal.get("ID") == animal_id:
                return animal

        return None

    except ApiError as e:
        raise RuntimeError(f"Failed to find animal {animal_id}: {e}")


def main():
    # Safety check for development environment
    guard_dev_only()

    try:
        creds = get_shelterluv_creds()
        api_key = creds["api_key"]
    except Exception as e:
        print(f"Failed to get ShelterLuv credentials: {e}", file=sys.stderr)
        return 1

    animal_id = "MVSF-A-56536"  # The specific animal ID from the URL

    try:
        animal = find_animal_by_id(api_key, animal_id)
        if animal:
            print(f"Animal ID: {animal.get('ID')}")
            print(f"Internal ID: {animal.get('Internal-ID')}")
            print(f"Name: {animal.get('Name')}")
            print(f"Status: {animal.get('Status')}")
            return 0
        else:
            print(f"Animal {animal_id} not found", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Failed to find animal {animal_id}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
Get a specific animal from ShelterLuv API by Internal-ID.
"""

import os
import sys
from typing import Dict, Any
from ..api import get_animal_by_internal_id
from ..errors import ApiError
from ..common import guard_dev_only
from ..secret_manager import get_shelterluv_creds

def get_animal_by_id(api_key: str, animal_id: str) -> Dict[str, Any]:
    """Fetch specific animal from ShelterLuv API by Internal-ID."""
    try:
        return get_animal_by_internal_id(animal_id, api_key)
    except ApiError as e:
        raise RuntimeError(f"Failed to get animal {animal_id}: {e}")

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
        animal = get_animal_by_id(api_key, animal_id)
        print(f"Animal ID: {animal.get('ID')}")
        print(f"Internal ID: {animal.get('Internal-ID')}")
        print(f"Name: {animal.get('Name')}")
        print(f"Status: {animal.get('Status')}")
        return 0
    except Exception as e:
        print(f"Failed to get animal {animal_id}: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    exit(main())

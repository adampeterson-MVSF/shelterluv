#!/usr/bin/env python3
"""
Example script for checking ShelterLuv API fields.
DO NOT commit this file with real API keys.
Copy this to check_api_fields.py and set your credentials via environment variables.
"""

import os

import requests

# API configuration - read from environment
BASE_URL = "https://new.shelterluv.com/api/v1"
API_KEY = os.getenv("SHELTERLUV_API_KEY")
ANIMAL_ID = os.getenv("SHELTERLUV_ANIMAL_ID", "56536")  # Example animal ID

if not API_KEY:
    print("Error: SHELTERLUV_API_KEY environment variable not set")
    exit(1)

headers = {"X-API-Key": API_KEY}

try:
    url = f"{BASE_URL}/animals/{ANIMAL_ID}"
    print(f"Fetching: {url}")

    response = requests.get(url, headers=headers, timeout=(3, 10))
    response.raise_for_status()

    data = response.json()
    animal = data.get("animal", {})

    print("Available fields in ShelterLuv API:")
    for key in sorted(animal.keys()):
        value = animal[key]
        if isinstance(value, str) and len(value) > 50:
            print(f"  {key}: {value[:50]}... (truncated)")
        else:
            print(f"  {key}: {value}")

    # Check for timestamp-related fields
    timestamp_fields = [
        k
        for k in animal.keys()
        if "time" in k.lower()
        or "date" in k.lower()
        or "updated" in k.lower()
        or "modified" in k.lower()
    ]
    if timestamp_fields:
        print(f"\nTimestamp-related fields: {timestamp_fields}")
    else:
        print("\nNo obvious timestamp fields found")

except Exception as e:
    print(f"Error: {e}")

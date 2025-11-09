#!/usr/bin/env python3
"""
Debug script to test ShelterLuv API connectivity.
"""

import os
import sys
import requests

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Validate required environment variables
required_env_vars = ['SHELTERLUV_USER', 'SHELTERLUV_PASS', 'SHELTERLUV_API_KEY']
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
    print("Set these in your .env file or environment before running this debug script.")
    sys.exit(1)

print("Testing ShelterLuv API connectivity...")

try:
    from secret_manager import get_shelterluv_creds
    creds = get_shelterluv_creds()
    print(f"Got credentials: user={creds['username']}, api_key length={len(creds['api_key'])}")

    # Test a simple API call
    print("Testing API call to /api/v1/animals...")
    headers = {'X-API-Key': creds["api_key"]}
    response = requests.get('https://new.shelterluv.com/api/v1/animals', headers=headers, timeout=10)
    print(f"API response status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"API response structure: {type(data)}")
        print(f"API response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")

        if isinstance(data, dict) and 'animals' in data:
            animals = data['animals']
            print(f"API returned {len(animals)} animals in 'animals' key")
            if animals:
                print(f"First animal: {animals[0].get('Name', 'Unknown')}")
        elif isinstance(data, list):
            print(f"API returned {len(data)} animals as list")
            if data:
                print(f"First animal: {data[0].get('Name', 'Unknown')}")
        else:
            print(f"Unexpected response structure: {data}")
    else:
        print(f"API error: {response.text}")

except Exception as e:
    print(f"API test failed: {e}")
    import traceback
    traceback.print_exc()

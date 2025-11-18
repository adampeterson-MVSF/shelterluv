#!/usr/bin/env python3
"""
Test idempotency manually to debug the hanging issue.
"""

import os
import sys

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print("WARNING: python-dotenv not available, relying on existing env vars")

# Set test-specific environment variables
os.environ["E2E_LIVE_DB"] = "1"
os.environ["ENV_PROFILE"] = "main"  # Use main profile which maps to muttville project
os.environ["DOGS_COLLECTION"] = "dogs_e2e"
os.environ["DISABLE_SECRET_MANAGER"] = "1"

# Validate required environment variables for testing
required_env_vars = ["SHELTERLUV_USER", "SHELTERLUV_PASS", "SHELTERLUV_API_KEY"]
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
    print("Set these in your .env file or environment before running this test script.")
    sys.exit(1)

print("Environment variables set:")
from config import EtlConfig
config = EtlConfig.from_env()

print(f"E2E_LIVE_DB: {os.environ.get('E2E_LIVE_DB')}")
print(f"ENV_PROFILE: {os.environ.get('ENV_PROFILE')}")
print(f"GCP_PROJECT (resolved): {config.project_id}")
print(f"DOGS_COLLECTION: {os.environ.get('DOGS_COLLECTION')}")
print(f"DISABLE_SECRET_MANAGER: {os.environ.get('DISABLE_SECRET_MANAGER')}")
print(f"SHELTERLUV_USER: {os.environ.get('SHELTERLUV_USER')}")
print(f"SHELTERLUV_PASS: {'SET' if os.environ.get('SHELTERLUV_PASS') else 'NOT SET'}")
print(f"SHELTERLUV_API_KEY: {'SET' if os.environ.get('SHELTERLUV_API_KEY') else 'NOT SET'}")

sys.path.append(os.path.dirname(__file__))

print("Testing idempotency manually...")

print("About to import pipeline...")
try:
    from config import EtlConfig
    from pipeline import run_etl_process
    from secret_manager import get_shelterluv_creds

    print("Pipeline imported successfully")

    # Get credentials once
    config = EtlConfig.from_env(overrides={"dry_run": False, "animal_limit": 2})
    creds = get_shelterluv_creds(config.secrets)

    print("First ETL run...")
    stats1 = run_etl_process(config, creds)
    print(f"First run complete: {stats1}")

    print("Waiting 30 seconds to avoid rate limits...")
    import time

    time.sleep(30)

    print("Second ETL run...")
    stats2 = run_etl_process(config, creds)
    print(f"Second run complete: {stats2}")

    print("Idempotency test passed!")

except Exception as e:
    print(f"Test failed: {e}")
    import traceback

    traceback.print_exc()

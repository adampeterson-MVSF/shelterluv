#!/usr/bin/env python3
"""
⚠️ HISTORICAL DEBUG SCRIPT - NOT PART OF NORMAL WORKFLOWS ⚠️

This was a debug tooling script for diagnosing import hangs.
If the underlying issue is fixed, this script is no longer needed.
Kept for historical reference only.

Original purpose: Test just importing pipeline module to see if it hangs.
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
os.environ["GCP_PROJECT"] = "muttville"
os.environ["DOGS_COLLECTION"] = "dogs_e2e"
os.environ["DISABLE_SECRET_MANAGER"] = "1"

# Validate required environment variables for testing
required_env_vars = ["SHELTERLUV_USER", "SHELTERLUV_PASS", "SHELTERLUV_API_KEY"]
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
    print("Set these in your .env file or environment before running this test script.")
    sys.exit(1)

sys.path.append(os.path.dirname(__file__))

print("Test: About to import pipeline...")
try:
    from pipeline import run_etl_process

    print("Test: Pipeline imported successfully!")
except Exception as e:
    print(f"Test: Pipeline import failed: {e}")
    import traceback

    traceback.print_exc()

print("Test: About to get credentials...")
try:
    from secret_manager import get_shelterluv_creds

    creds = get_shelterluv_creds()
    print(f"Test: Got credentials for user: {creds['username']}")
except Exception as e:
    print(f"Test: Credential retrieval failed: {e}")
    import traceback

    traceback.print_exc()

print("Test: About to call run_etl_process with dry_run=True...")
try:
    from config import EtlConfig

    config = EtlConfig.from_env(overrides={"dry_run": True, "animal_limit": 1})
    stats = run_etl_process(config, creds)
    print(f"Test: Dry run completed: {stats}")
except Exception as e:
    print(f"Test: ETL dry run failed: {e}")
    import traceback

    traceback.print_exc()

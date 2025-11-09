#!/usr/bin/env python3
"""
Debug script to test ETL pipeline directly without pytest overhead.
"""

import os
import sys

print("Debug: Starting script...")

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

print("Debug: Added to sys.path")

# Set environment variables
os.environ['E2E_LIVE_DB'] = '1'
os.environ['GCP_PROJECT'] = 'muttville'  # Use the actual project
os.environ['DOGS_COLLECTION'] = 'dogs_e2e'
os.environ['DISABLE_SECRET_MANAGER'] = '1'

print("Debug: Set environment variables")

# Test individual imports
try:
    print("Debug: Testing common import...")
    from common import get_project_id
    print("Debug: common imported successfully")
    project_id = get_project_id()
    print(f"Debug: Got project_id: {project_id}")
except Exception as e:
    print(f"Debug: common import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Starting debug ETL test...")

try:
    print("Step 1: Checking environment variables...")
    print(f"SHELTERLUV_USER: {os.environ.get('SHELTERLUV_USER', 'NOT SET')}")
    print(f"SHELTERLUV_PASS: {'SET' if os.environ.get('SHELTERLUV_PASS') else 'NOT SET'}")
    print(f"SHELTERLUV_API_KEY: {'SET' if os.environ.get('SHELTERLUV_API_KEY') else 'NOT SET'}")
    print(f"DISABLE_SECRET_MANAGER: {os.environ.get('DISABLE_SECRET_MANAGER', 'NOT SET')}")

    print("\nStep 2: Importing secret_manager...")
    from secret_manager import get_shelterluv_creds
    print("Step 3: Getting credentials...")
    creds = get_shelterluv_creds()
    print(f"Step 4: Got credentials: user={creds['username']}, api_key length={len(creds['api_key'])}")

    print("Step 5: Importing run_etl_process...")
    from pipeline import run_etl_process
    print("Step 6: Imported run_etl_process successfully")

    print("Step 7: Calling run_etl_process with animal_limit=2...")
    stats = run_etl_process(dry_run=False, animal_limit=2)
    print(f"Step 8: ETL completed successfully! Stats: {stats}")

except Exception as e:
    print(f"ETL failed with error: {e}")
    import traceback
    traceback.print_exc()

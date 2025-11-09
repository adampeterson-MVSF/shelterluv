#!/usr/bin/env python3
"""
Minimal debug script to isolate the hanging issue.
"""

import os
import sys

print("Debug ETL Minimal: Starting...")

# Set environment variables BEFORE any other imports (same as original)
os.environ['E2E_LIVE_DB'] = '1'
os.environ['GCP_PROJECT'] = 'muttville'  # Use the actual project
os.environ['DOGS_COLLECTION'] = 'dogs_e2e'
os.environ['DISABLE_SECRET_MANAGER'] = '1'

print("Debug ETL Minimal: Environment variables set")

# Add current directory to path for imports (same as original)
sys.path.append(os.path.dirname(__file__))
print("Debug ETL Minimal: Added to sys.path")

print("Debug ETL Minimal: About to import secret_manager...")
from secret_manager import get_shelterluv_creds
print("Debug ETL Minimal: secret_manager imported")

print("Debug ETL Minimal: Getting credentials...")
creds = get_shelterluv_creds()
print(f"Debug ETL Minimal: Got credentials: user={creds['username']}")

print("Debug ETL Minimal: Success!")

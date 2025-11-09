#!/usr/bin/env python3
"""
Simplified debug script to isolate the hanging issue.
"""

import os
import sys

print("Debug ETL Simple: Starting...")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("WARNING: python-dotenv not available, relying on existing env vars")

# Set test-specific environment variables
os.environ['E2E_LIVE_DB'] = '1'
os.environ['GCP_PROJECT'] = 'muttville'
os.environ['DOGS_COLLECTION'] = 'dogs_e2e'
os.environ['DISABLE_SECRET_MANAGER'] = '1'

# Validate required environment variables for testing
required_env_vars = ['SHELTERLUV_USER', 'SHELTERLUV_PASS', 'SHELTERLUV_API_KEY']
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
    print("Set these in your .env file or environment before running this debug script.")
    sys.exit(1)

print("Debug ETL Simple: Environment variables set")

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))
print("Debug ETL Simple: Added to sys.path")

print("Debug ETL Simple: About to import secret_manager...")
from secret_manager import get_shelterluv_creds
print("Debug ETL Simple: secret_manager imported")

print("Debug ETL Simple: Getting credentials...")
creds = get_shelterluv_creds()
print(f"Debug ETL Simple: Got credentials for user: {creds['username']}")

print("Debug ETL Simple: Success!")

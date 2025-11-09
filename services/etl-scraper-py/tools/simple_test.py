#!/usr/bin/env python3
import os
import sys

print("Simple test starting...")

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("WARNING: python-dotenv not available, relying on existing env vars")

# Validate required environment variables for testing
required_env_vars = ['SHELTERLUV_USER', 'SHELTERLUV_PASS', 'SHELTERLUV_API_KEY']
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
    print("Set these in your .env file or environment before running this test script.")
    sys.exit(1)

print("Environment variables set")

try:
    print("Testing basic import...")
    import secret_manager
    print("secret_manager imported successfully")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()

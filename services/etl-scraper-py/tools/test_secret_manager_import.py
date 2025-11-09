#!/usr/bin/env python3
"""
Test secret_manager import in isolation.
"""

import os
import sys

print("Setting environment variables...")
os.environ['DISABLE_SECRET_MANAGER'] = '1'
os.environ['E2E_LIVE_DB'] = '1'
# Don't set GCP_PROJECT to see if that causes issues

sys.path.append(os.path.dirname(__file__))

print("About to import secret_manager...")
try:
    import secret_manager
    print("secret_manager imported successfully!")
    print(f"PROJECT_ID: {secret_manager.PROJECT_ID}")
except Exception as e:
    print(f"secret_manager import failed: {e}")
    import traceback
    traceback.print_exc()

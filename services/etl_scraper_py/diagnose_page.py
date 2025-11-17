#!/usr/bin/env python3
"""
Diagnostic script to inspect ShelterLuv page structure.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scraper.session import ShelterLuvSession

def main():
    print("🔍 Diagnosing ShelterLuv page structure...")

    # Get credentials from env (since we can't use GCP secrets locally)
    username = os.environ.get("SHELTERLUV_USER")
    password = os.environ.get("SHELTERLUV_PASS")

    if not username or not password:
        print("❌ Set SHELTERLUV_USER and SHELTERLUV_PASS environment variables")
        return 1

    print(f"✅ Got credentials for user: {username}")

    try:
        with ShelterLuvSession(username, password) as session:
            page = session.page
            print("✅ Logged in successfully")

            # Navigate to animals dashboard
            print("🌐 Navigating to dashboard...")
            page.goto("https://new.shelterluv.com/dashboard?tab=animals", wait_until="domcontentloaded", timeout=30000)

            # Wait for page to load
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                page.wait_for_load_state("domcontentloaded", timeout=5000)
            page.wait_for_timeout(3000)

            # Check for "In Custody View" button
            in_custody_button = page.locator("text=In Custody View")
            if in_custody_button.count() > 0:
                print("✅ Found 'In Custody View' button")
                in_custody_button.first.click()
                page.wait_for_timeout(2000)
            else:
                print("❌ 'In Custody View' button not found")

            # Check for animal rows
            animal_rows = page.locator('[data-cy^="animal-row-"]')
            count = animal_rows.count()
            print(f"📊 Found {count} elements with data-cy starting with 'animal-row-'")

            # Check for table rows
            tbody_rows = page.locator("tbody tr")
            tbody_count = tbody_rows.count()
            print(f"📊 Found {tbody_count} table rows (tbody tr)")

            # Check page title and URL
            print(f"📄 Page title: {page.title()}")
            print(f"🔗 Current URL: {page.url}")

            # Get some sample HTML
            if tbody_count > 0:
                first_row = tbody_rows.first
                html = first_row.inner_html()
                print(f"📝 First table row HTML (truncated): {html[:200]}...")
            else:
                # Get general page content
                body_html = page.locator("body").inner_html()
                print(f"📝 Body HTML (first 500 chars): {body_html[:500]}...")

            # Check for any MVSF-A- text
            page_text = page.inner_text()
            if "MVSF-A-" in page_text:
                print("✅ Found MVSF-A- text on page")
                # Count occurrences
                count = page_text.count("MVSF-A-")
                print(f"📊 Found {count} instances of MVSF-A-")
            else:
                print("❌ No MVSF-A- text found on page")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())

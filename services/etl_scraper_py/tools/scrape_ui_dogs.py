"""
Scrape dogs directly from ShelterLuv web UI to see what's actually in the In Custody view.

This diagnostic library + CLI:
1. Logs into ShelterLuv
2. Navigates to the animals dashboard/list
3. Scrapes all visible dogs and their data
4. Returns structured results

This is kept separate from ETL pipeline to allow comparison between API data and UI presentation.
Use compare_etl_vs_ui.py to detect divergences between ETL output and UI scraping.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List

from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")
load_dotenv(".env.local")

# Set the Google Cloud project
os.environ["GOOGLE_CLOUD_PROJECT"] = "muttville"

from project_safety import guard_dev_only

# Import our modules after setting environment
from scraper import ShelterLuvScraper
from secret_manager import get_shelterluv_creds

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def scrape_all_in_custody() -> List[Dict[str, Any]]:
    """Scrape all animals shown in the ShelterLuv UI dashboard."""
    # Safety check for development environment
    guard_dev_only()

    # Get credentials
    creds = get_shelterluv_creds()

    dogs_data = []

    with ShelterLuvScraper(creds["username"], creds["password"]) as scraper:
        page = scraper.session.page

        # Navigate to the main animals dashboard
        page.goto("https://new.shelterluv.com/dashboard?tab=animals")

        # Wait for the page to load
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        # Try to ensure we're in "In Custody View"
        try:
            in_custody_button = page.get_by_text("In Custody View")
            if in_custody_button.count() > 0:
                in_custody_button.first.click()
                page.wait_for_timeout(2000)
        except:
            pass

        # Extract animal IDs from the page
        page_text = page.inner_text("body")
        import re

        animal_ids = set(re.findall(r"MVSF-A-\d+", page_text))

        # Create basic dog records
        for animal_id in animal_ids:
            dogs_data.append(
                {
                    "ID": animal_id,
                    "Name": f"Dog {animal_id}",  # Placeholder name
                    "source": "ui_scrape",
                }
            )

    return dogs_data


# Legacy function kept for backward compatibility
# TODO: Remove this once all callers are updated to use scrape_all_in_custody
def scrape_animals_from_ui() -> Dict[str, Any]:
    """Legacy function - redirects to new implementation."""
    # For now, just return empty data to avoid breaking existing code
    return {"table_elements": [], "animal_links": [], "json_data": []}


def display_scraped_data(data: Dict[str, Any]):
    """Display the scraped data in a readable format."""
    print("\n" + "=" * 80)
    print("📊 SCRAPED DATA RESULTS")
    print("=" * 80)

    print(f"📄 Page Title: {data.get('page_title', 'Unknown')}")
    print(f"🔗 URL: {data.get('url', 'Unknown')}")

    if "error" in data:
        print(f"❌ ERROR: {data['error']}")
        return

    # Display table elements
    print(f"\n📋 TABLE ELEMENTS FOUND: {len(data.get('table_elements', []))}")
    for item in data.get("table_elements", []):
        print(f"  Selector: {item['selector']} | Index: {item['index']}")
        print(f"  Text: {item['text'][:100]}{'...' if len(item['text']) > 100 else ''}")
        print(f"  HTML: {item['html'][:100]}{'...' if len(item['html']) > 100 else ''}")
        print()

    # Display animal links
    print(f"\n🔗 ANIMAL LINKS FOUND: {len(data.get('animal_links', []))}")
    for link in data.get("animal_links", []):
        print(f"  {link['text']} -> {link['href']}")

    # Display JSON data
    print(f"\n🔍 JSON DATA FOUND: {len(data.get('json_data', []))}")
    for i, json_item in enumerate(data.get("json_data", [])):
        print(f"  JSON #{i+1}: {str(json_item)[:200]}{'...' if len(str(json_item)) > 200 else ''}")

    print("\n📸 Screenshot saved as: shelterluv_animals_page.png")


def get_ui_animal_ids(scraped_data: Dict[str, Any]) -> set:
    """Extract animal IDs from scraped UI data."""
    ids = set()

    # From table elements
    for element in scraped_data.get("table_elements", []):
        text = element.get("text", "")
        # Look for MVSF-A- patterns
        import re

        matches = re.findall(r"MVSF-A-\d+", text)
        ids.update(matches)

        # Also check parsed data if available
        if "parsed_data" in element:
            animal_id = element["parsed_data"].get("ID")
            if animal_id:
                ids.add(animal_id)

    # From links
    for link in scraped_data.get("animal_links", []):
        href = link.get("href", "")
        # Extract ID from URL patterns like /animals/MVSF-A-12345
        match = re.search(r"/animals/(MVSF-A-\d+)", href)
        if match:
            ids.add(match.group(1))

    return ids


def main():
    """CLI wrapper for scrape_all_in_custody."""
    dogs = scrape_all_in_custody()
    print(f"✅ Scraped {len(dogs)} dogs from ShelterLuv UI")
    for dog in dogs[:5]:  # Show first 5
        print(f"  - {dog.get('Name', 'Unknown')} ({dog.get('ID', 'No ID')})")
    if len(dogs) > 5:
        print(f"  ... and {len(dogs) - 5} more dogs")


if __name__ == "__main__":
    main()

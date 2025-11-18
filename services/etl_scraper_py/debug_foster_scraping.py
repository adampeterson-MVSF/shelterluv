#!/usr/bin/env python3
"""
Debug script to troubleshoot foster information scraping for a specific dog.

This script logs into ShelterLuv and checks the foster information extraction
for the California Love dog profile: https://new.shelterluv.com/animal/MVSF-A-56497
"""

import os
import sys
import time
from typing import Any, Dict

# Add the scraper directory to the path
sys.path.append(os.path.dirname(__file__))

from playwright.sync_api import sync_playwright
from scraper.parsers_foster import scrape_foster_info


def debug_foster_scraping(username: str, password: str, animal_id: str = "MVSF-A-56497"):
    """
    Debug foster scraping for a specific animal profile.

    Args:
        username: ShelterLuv username
        password: ShelterLuv password
        animal_id: Animal ID to check (default: California Love)
    """

    print(f"🔍 Debugging foster scraping for animal: {animal_id}")
    print("=" * 60)

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # Keep visible for debugging
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate to ShelterLuv login
            print("🌐 Navigating to ShelterLuv login...")
            page.goto("https://new.shelterluv.com")

            # Wait for login form
            page.wait_for_selector('input[name="username"]', timeout=10000)

            # Fill login credentials
            print("🔐 Logging in...")
            page.fill('input[name="username"]', username)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')

            # Wait for login to complete
            page.wait_for_load_state("networkidle")
            print("✅ Login successful")

            # Navigate to the specific animal profile
            animal_url = f"https://new.shelterluv.com/animal/{animal_id}"
            print(f"🐕 Navigating to animal profile: {animal_url}")
            page.goto(animal_url)

            # Wait for page to load
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(2000)

            print("📊 Current page info:")
            print(f"   URL: {page.url}")
            print(f"   Title: {page.title()}")

            # Check if we're on the right page
            if animal_id not in page.url:
                print(f"❌ Wrong page! Expected to be on animal/{animal_id} but got: {page.url}")
                return

            print("✅ On correct animal profile page")

            # Take a screenshot for reference
            screenshot_path = f"debug_screenshot_{animal_id}.png"
            page.screenshot(path=screenshot_path)
            print(f"📸 Screenshot saved to: {screenshot_path}")

            # Wait for Livewire components to load
            print("⏳ Waiting for dynamic content to load...")
            try:
                page.locator('[wire\\:id]').first.wait_for(timeout=15000)
                print("✅ Livewire components loaded")
            except Exception as e:
                print(f"⚠️  Livewire components not found or timeout: {e}")

            # Additional wait for AJAX content
            page.wait_for_timeout(5000)

            # Debug: Look for any elements containing "Foster"
            print("\n🔍 Searching for 'Foster' text on page...")
            foster_elements = page.locator('text=/Foster/i').all()
            print(f"Found {len(foster_elements)} elements containing 'Foster'")

            for i, elem in enumerate(foster_elements[:10]):  # Limit to first 10
                try:
                    text = elem.inner_text(timeout=2000).strip()
                    print(f"   [{i}] '{text[:100]}{'...' if len(text) > 100 else ''}'")
                except Exception as e:
                    print(f"   [{i}] Error getting text: {e}")

            # Look for the specific selector from user's HTML
            print("\n🔍 Checking for exact foster selector...")
            exact_selectors = page.locator('div.flex.items-center.text-body-2.gap-2').all()
            print(f"Found {len(exact_selectors)} elements with exact selector")

            for i, container in enumerate(exact_selectors):
                try:
                    text_content = container.inner_text(timeout=2000).strip()
                    print(f"   Container {i}: '{text_content}'")
                    if 'Foster:' in text_content:
                        print("   🎯 FOUND FOSTER INFO!")
                        # Look for links in this container
                        links = container.locator('a').all()
                        for j, link in enumerate(links):
                            try:
                                href = link.get_attribute('href', timeout=1000)
                                link_text = link.inner_text(timeout=1000).strip()
                                print(f"      Link {j}: '{link_text}' -> {href}")
                            except Exception as e:
                                print(f"      Link {j} error: {e}")
                except Exception as e:
                    print(f"   Container {i} error: {e}")

            # Try the actual scraping function
            print("\n🔧 Running foster scraping function...")
            start_time = time.time()
            foster_result = scrape_foster_info(page)
            end_time = time.time()

            print(".2f")
            print(f"Result: {foster_result}")

            if foster_result:
                print("✅ Foster info found!")
                for key, value in foster_result.items():
                    print(f"   {key}: {value}")
            else:
                print("❌ No foster info found")

            # Additional debugging: check page HTML for foster-related content
            print("\n🔍 Checking page HTML for foster patterns...")
            page_html = page.content()
            foster_patterns = [
                'Foster:',
                'foster',
                'MVSF-P-',  # Person ID pattern
                'Wendy Hamilton',  # The specific foster name from user's example
            ]

            for pattern in foster_patterns:
                count = page_html.upper().count(pattern.upper())
                if count > 0:
                    print(f"   '{pattern}': found {count} times")

            # Look for person links
            person_links = page.locator('a[href*="person/"]').all()
            print(f"\n🔗 Found {len(person_links)} person profile links:")
            for i, link in enumerate(person_links[:5]):  # Show first 5
                try:
                    href = link.get_attribute('href', timeout=1000)
                    text = link.inner_text(timeout=1000).strip()
                    print(f"   [{i}] {text} -> {href}")
                except Exception as e:
                    print(f"   [{i}] Error: {e}")

        except Exception as e:
            print(f"❌ Error during debugging: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Keep browser open for manual inspection if needed
            input("\nPress Enter to close browser...")
            browser.close()


def main():
    """Main function to run the debug script."""

    # Get credentials from environment variables
    username = os.environ.get('SHELTERLUV_USERNAME')
    password = os.environ.get('SHELTERLUV_PASSWORD')

    if not username or not password:
        print("❌ Please set SHELTERLUV_USERNAME and SHELTERLUV_PASSWORD environment variables")
        print("Example:")
        print("  export SHELTERLUV_USERNAME='your_username'")
        print("  export SHELTERLUV_PASSWORD='your_password'")
        sys.exit(1)

    # Get animal ID from command line or use default
    animal_id = sys.argv[1] if len(sys.argv) > 1 else "MVSF-A-56497"

    debug_foster_scraping(username, password, animal_id)


if __name__ == "__main__":
    main()

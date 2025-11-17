"""
Scraper for extracting Internal IDs from ShelterLuv's In Custody view.

This module provides functions to scrape all Internal IDs currently
shown in the "In Custody View" table by parsing the web UI directly.
"""

from typing import Dict, Set

from errors import ScraperError

from .session import ShelterLuvSession


def _collect_ids_from_current_page(page) -> Set[str]:
    """
    Extract Internal IDs from the current page's table rows.
    Used for testing the table parsing logic.
    """
    ids = set()

    # Find table rows (tbody tr elements)
    tbody_rows = page.locator("tbody tr")
    row_count = tbody_rows.count()

    for i in range(row_count):
        row = tbody_rows.nth(i)

        # Extract cells from this row
        cells = row.locator("td")

        try:
            # Internal-ID is typically in the 3rd column (index 2)
            internal_id_cell = cells.nth(2)
            internal_id_text = internal_id_cell.text_content().strip()

            # Validate it's a numeric ID
            if internal_id_text and internal_id_text.isdigit():
                ids.add(internal_id_text)

        except Exception:
            # Skip malformed rows
            continue

    return ids


def _has_next_page(page) -> bool:
    """
    Check if there's a next page button that's enabled.
    Used for testing pagination logic.
    """
    try:
        # Look for next page button
        next_button = page.locator(
            'button:has-text("Next"), [aria-label*="next"], .pagination .next'
        )

        if next_button.count() > 0:
            button = next_button.first
            # Check if button is enabled (not disabled, not aria-disabled=true)
            is_disabled = (
                button.get_attribute("disabled") is not None
                or button.get_attribute("aria-disabled") == "true"
                or "disabled" in (button.get_attribute("class") or "")
            )
            return not is_disabled

        return False

    except Exception:
        return False


def scrape_in_custody_ids(username: str, password: str) -> Set[str]:
    """
    Scrape all ShelterLuv Internal IDs from the ShelterLuv In Custody view by parsing the web UI.

    This function navigates to the ShelterLuv dashboard, ensures we're in "In Custody View",
    and extracts ShelterLuv Internal IDs from data-cy attributes on animal rows.

    Args:
        username: ShelterLuv login username
        password: ShelterLuv login password

    Returns:
        Set of ShelterLuv Internal IDs (strings) currently in custody

    Raises:
        ScraperError: If scraping fails
    """
    # Get the full data and extract just IDs for backward compatibility
    full_data = scrape_in_custody_data(username, password)
    return set(full_data.keys())


def scrape_in_custody_data(username: str, password: str) -> Dict[str, Dict[str, str]]:
    """
    Scrape all ShelterLuv animal data from the ShelterLuv In Custody view by parsing the web UI.

    This function navigates to the ShelterLuv dashboard, ensures we're in "In Custody View",
    and extracts comprehensive data for each animal from the table rows.

    Args:
        username: ShelterLuv login username
        password: ShelterLuv login password

    Returns:
        Dict mapping ShelterLuv Internal IDs to dicts containing:
        - Intake: Intake date
        - Name: Animal name
        - ID: ShelterLuv ID
        - Species: Animal species
        - Breed: Animal breed
        - Color: Animal color
        - Sex: Animal sex
        - Age: Animal age
        - Location: Current location
        - Status: Animal status

    Raises:
        ScraperError: If scraping fails
    """
    try:
        animal_data = {}

        with ShelterLuvSession(username, password) as session:
            page = session.page

            # Navigate to the animals dashboard
            page.goto(
                "https://new.shelterluv.com/dashboard?tab=animals",
                wait_until="domcontentloaded",
                timeout=30000,
            )

            # Wait for the page to load (with timeout to avoid hanging)
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                # If networkidle times out, use domcontentloaded as fallback
                page.wait_for_load_state("domcontentloaded", timeout=5000)
            page.wait_for_timeout(3000)  # Extra wait for dynamic content

            # Ensure we're in "In Custody View"
            try:
                in_custody_button = page.get_by_text("In Custody View")
                if in_custody_button.count() > 0:
                    in_custody_button.first.click()
                    page.wait_for_timeout(2000)
            except Exception:
                pass  # May already be active

            # Wait for content to load
            page.wait_for_timeout(2000)

            # Try multiple strategies to find animal rows
            animal_data = {}

            # Strategy 1: Try the current data-cy approach
            animal_rows = page.locator('[data-cy^="animal-row-"]')
            animal_count = animal_rows.count()

            if animal_count == 0:
                # Strategy 2: If no data-cy attributes, try table rows
                print("No data-cy attributes found, trying table rows...")
                animal_rows = page.locator("tbody tr")
                animal_count = animal_rows.count()
                print(f"Found {animal_count} table rows")

            print(f"Using {animal_count} animal rows for processing")

            for i in range(min(animal_count, 200)):  # Limit to 200 for safety
                try:
                    row = animal_rows.nth(i)

                    # Extract ShelterLuv internal ID - try multiple methods
                    shelterluv_id = None

                    # Method 1: From data-cy attribute
                    data_cy = row.get_attribute("data-cy")
                    if data_cy and data_cy.startswith("animal-row-"):
                        shelterluv_id = data_cy.replace("animal-row-", "")
                    else:
                        # Method 2: Look for MVSF-A- in links
                        muttville_links = row.locator('a[href*="/animal/MVSF-A-"]')
                        if muttville_links.count() > 0:
                            href = muttville_links.first.get_attribute("href")
                            if href and "/animal/MVSF-A-" in href:
                                # Extract ID from URL like /animal/MVSF-A-12345
                                parts = href.split("MVSF-A-")
                                if len(parts) > 1:
                                    shelterluv_id = parts[1].split('/')[0]
                        else:
                            # Method 3: Look for MVSF-A- in text and extract number
                            row_text = row.inner_text()
                            if "MVSF-A-" in row_text:
                                # Find the pattern MVSF-A- followed by digits
                                import re
                                match = re.search(r'MVSF-A-(\d+)', row_text)
                                if match:
                                    shelterluv_id = match.group(1)

                    if not shelterluv_id:
                        continue  # Skip rows without identifiable IDs

                    # Extract basic data - try to get as much as possible
                    row_data = {"Internal-ID": shelterluv_id}

                    try:
                        # Look for name and other data
                        links = row.locator('a')
                        if links.count() > 0:
                            first_link = links.first
                            link_text = first_link.inner_text().strip()
                            if link_text and "MVSF-A-" in link_text:
                                row_data["Name"] = link_text

                        # Get all text from the row for status detection
                        row_text = row.inner_text()
                        row_data["RawText"] = row_text

                        # Try to extract status - look for common status words
                        text_lower = row_text.lower()
                        if "available" in text_lower:
                            row_data["Status"] = "AVAILABLE"
                        elif "pending" in text_lower:
                            row_data["Status"] = "PENDING"
                        elif "hold" in text_lower:
                            row_data["Status"] = "HOLD"
                        elif "adopted" in text_lower:
                            row_data["Status"] = "ADOPTED"
                        else:
                            row_data["Status"] = "UNKNOWN"

                    except Exception as e:
                        # If data extraction fails, at least store the ID
                        row_data["Status"] = "UNKNOWN"

                    # Store the animal data
                    animal_data[shelterluv_id] = row_data

                except Exception:
                    continue  # Skip malformed rows

            return animal_data

    except Exception as e:
        raise ScraperError(f"Failed to scrape in-custody data from UI: {e}")

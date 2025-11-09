"""
Scraper for extracting Internal IDs from ShelterLuv's In Custody view.

This module provides functions to scrape all Internal IDs currently
shown in the "In Custody View" table by parsing the web UI directly.
"""

import logging
from typing import Set, Dict
from scraper import ShelterLuvScraper
from errors import ScraperError

logger = logging.getLogger(__name__)


def _collect_ids_from_current_page(page) -> Set[str]:
    """
    Extract Internal IDs from the current page's table rows.
    Used for testing the table parsing logic.
    """
    ids = set()

    # Find table rows (tbody tr elements)
    tbody_rows = page.locator('tbody tr')
    row_count = tbody_rows.count()

    for i in range(row_count):
        row = tbody_rows.nth(i)

        # Extract cells from this row
        cells = row.locator('td')

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
        next_button = page.locator('button:has-text("Next"), [aria-label*="next"], .pagination .next')

        if next_button.count() > 0:
            button = next_button.first
            # Check if button is enabled (not disabled, not aria-disabled=true)
            is_disabled = (
                button.get_attribute('disabled') is not None or
                button.get_attribute('aria-disabled') == 'true' or
                'disabled' in (button.get_attribute('class') or '')
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

    logger.info("Scraping in-custody IDs from ShelterLuv web UI")

    try:
        ids = set()

        with ShelterLuvScraper(username, password) as scraper:
            page = scraper.session.page

            # Navigate to the animals dashboard
            logger.debug("Navigating to ShelterLuv animals dashboard")
            page.goto("https://new.shelterluv.com/dashboard?tab=animals")

            # Wait for the page to load
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(3000)  # Extra wait for dynamic content

            # Ensure we're in "In Custody View"
            logger.debug("Ensuring 'In Custody View' is active")
            try:
                in_custody_button = page.get_by_text("In Custody View")
                if in_custody_button.count() > 0:
                    logger.debug("Clicking 'In Custody View' button")
                    in_custody_button.first.click()
                    page.wait_for_timeout(2000)
                else:
                    logger.debug("'In Custody View' button not found - may already be active")
            except Exception as e:
                logger.warning(f"Could not click In Custody View: {e}")

            # Wait for content to load
            page.wait_for_timeout(2000)

            # Parse animals from the DOM using data-cy attributes
            logger.debug("Extracting animal IDs from DOM")

            # Find all animal row elements with data-cy attributes
            animal_rows = page.locator('[data-cy^="animal-row-"]')
            animal_count = animal_rows.count()
            logger.debug(f"Found {animal_count} animal rows with data-cy attributes")

            for i in range(min(animal_count, 100)):  # Limit to 100 for safety
                try:
                    row = animal_rows.nth(i)
                    data_cy = row.get_attribute('data-cy')

                    if data_cy and data_cy.startswith('animal-row-'):
                        # Extract ShelterLuv internal ID from data-cy attribute
                        shelterluv_id = data_cy.replace('animal-row-', '')

                        # Verify this is actually an in-custody animal by checking for Muttville ID
                        muttville_links = row.locator('a[href*="/animal/MVSF-A-"]')
                        if muttville_links.count() > 0:
                            href = muttville_links.first.get_attribute('href')
                            if href and '/animal/MVSF-A-' in href:
                                # Extract Muttville ID from URL
                                muttville_id = href.split('/animal/')[-1]
                                logger.debug(f"Found in-custody animal: ShelterLuv ID {shelterluv_id} (Muttville: {muttville_id})")
                                ids.add(shelterluv_id)
                        else:
                            # Fallback: try to find MVSF-A- text in the row
                            row_text = row.inner_text()
                            if 'MVSF-A-' in row_text:
                                lines = row_text.split('\n')
                                for line in lines:
                                    line = line.strip()
                                    if line.startswith('MVSF-A-'):
                                        muttville_id = line
                                        logger.debug(f"Found in-custody animal (text): ShelterLuv ID {shelterluv_id} (Muttville: {muttville_id})")
                                        ids.add(shelterluv_id)
                                        break

                except Exception as e:
                    logger.warning(f"Error processing animal row {i}: {e}")
                    continue

            logger.info(f"Successfully scraped {len(ids)} animal IDs from UI")

            return ids

    except Exception as e:
        raise ScraperError(f"Failed to scrape in-custody IDs from UI: {e}")


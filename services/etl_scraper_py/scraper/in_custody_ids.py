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

            # Parse animals from the DOM using data-cy attributes
            # Find all animal row elements with data-cy attributes
            animal_rows = page.locator('[data-cy^="animal-row-"]')
            animal_count = animal_rows.count()

            for i in range(min(animal_count, 200)):  # Limit to 200 for safety
                try:
                    row = animal_rows.nth(i)
                    data_cy = row.get_attribute("data-cy")

                    if data_cy and data_cy.startswith("animal-row-"):
                        # Extract ShelterLuv internal ID from data-cy attribute
                        shelterluv_id = data_cy.replace("animal-row-", "")

                        # Verify this is actually an in-custody animal by checking for Muttville ID
                        is_muttville_animal = False
                        muttville_links = row.locator('a[href*="/animal/MVSF-A-"]')
                        if muttville_links.count() > 0:
                            href = muttville_links.first.get_attribute("href")
                            if href and "/animal/MVSF-A-" in href:
                                is_muttville_animal = True
                        else:
                            # Fallback: try to find MVSF-A- text in the row
                            row_text = row.inner_text()
                            if "MVSF-A-" in row_text:
                                is_muttville_animal = True

                        if not is_muttville_animal:
                            continue  # Skip non-Muttville animals

                        # Extract data from the grid-based layout using specific selectors
                        row_data = {}

                        try:
                            # Intake date (hidden on smaller screens, lg:inline-flex)
                            intake_elem = row.locator("div.col-span-2.hidden.lg\\:inline-flex")
                            intake_text = (
                                intake_elem.inner_text().strip() if intake_elem.count() > 0 else ""
                            )
                            row_data["Intake"] = intake_text

                            # Name from the link - be more specific to avoid the profile photo link
                            name_link = row.locator("a.group.link")
                            name_text = (
                                name_link.inner_text().strip() if name_link.count() > 0 else ""
                            )
                            row_data["Name"] = name_text

                            # ID from the specific div with the right class
                            id_elem = row.locator("div.sm\\:col-span-2")
                            row_data["ID"] = (
                                id_elem.inner_text().strip() if id_elem.count() > 0 else ""
                            )

                            # For now, let's just extract what we can reliably get
                            # The table structure is complex and may vary
                            # We'll get the detailed data during profile scraping instead

                            # Species - try to find "Dog" text
                            species_texts = row.locator("div").all()
                            for div in species_texts[:10]:  # Check first 10 divs
                                text = div.inner_text().strip()
                                if text == "Dog" or text == "Cat":
                                    row_data["Species"] = text
                                    break

                            # Age - look for patterns like "12Y/0M/22D"
                            age_candidates = row.locator("div")
                            for i in range(min(age_candidates.count(), 10)):
                                text = age_candidates.nth(i).inner_text().strip()
                                if "Y/" in text and "M/" in text:
                                    row_data["Age"] = text
                                    break

                            # Sex - look for Male/Female
                            sex_candidates = row.locator("div")
                            for i in range(min(sex_candidates.count(), 10)):
                                text = sex_candidates.nth(i).inner_text().strip()
                                if text in ["Male", "Female"]:
                                    row_data["Sex"] = text
                                    break

                            # Status - look for Available/Adopted/etc. and map to schema enums
                            status_candidates = row.locator("p")
                            for i in range(min(status_candidates.count(), 5)):
                                text = status_candidates.nth(i).inner_text().strip()
                                if text == "Available":
                                    row_data["Status"] = "AVAILABLE"
                                    break
                                elif text == "Adopted":
                                    row_data["Status"] = "ADOPTED"
                                    break
                                elif text == "Pending":
                                    row_data["Status"] = "PENDING"
                                    break
                                elif text == "Hold":
                                    row_data["Status"] = "HOLD"
                                    break

                        except Exception as e:
                            # If extraction fails, continue with minimal data
                            row_data = {"FoundInUI": True, "ShelterLuvID": shelterluv_id}

                        animal_data[shelterluv_id] = row_data

                except Exception:
                    continue  # Skip malformed rows

            return animal_data

    except Exception as e:
        raise ScraperError(f"Failed to scrape in-custody data from UI: {e}")

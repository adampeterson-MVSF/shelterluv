"""
Field-level parsing functions for basic profile information.
Handles core attributes like name, ID, physical characteristics, etc.
"""

from typing import Any, Dict

from .navigation import SELECTORS


def scrape_profile_main_content(page) -> str:
    """Scrape the main profile content, including categories section."""
    # First try to get the case manager section
    main_content = page.locator(SELECTORS["case_manager_section"])
    if main_content.count() > 0:
        case_manager_text = main_content.first.inner_text(timeout=5000)  # type: ignore
    else:
        case_manager_text = ""

    # Also try to get the categories section which might be separate
    # Look for the div containing the Categories header
    categories_content = page.locator('div:has-text("Categories")')
    if categories_content.count() > 0:
        # Only get the inner text, not the full HTML to avoid size issues
        categories_text = categories_content.first.inner_text(timeout=3000)  # type: ignore
    else:
        categories_text = ""

    # Combine both sections
    full_text = f"{case_manager_text}\n\n{categories_text}".strip()
    return full_text


def scrape_overview_fields(page, navigation) -> Dict[str, str]:
    """Scrape overview section fields using robust XPath selectors: Species, Breed, Color, Pattern, Distinguishing Marks, Adoption Price."""
    result = {}

    # Field mappings: label text -> schema field name
    field_mappings = {
        "Species": "Species",
        "Breed": "Breed",  # Already handled by API, but keep for consistency
        "Color": "Color",
        "Pattern": "Pattern",
        "Distinguishing Marks": "DistinguishingMarks",
        "Adoption Price": "AdoptionPrice",
    }

    for label_text, field_name in field_mappings.items():
        try:
            # Look for the label followed by its value
            label_locator = page.locator(f'text="{label_text}"')
            if label_locator.count() > 0:
                # Find the parent container that holds both label and value
                container = label_locator.first.locator('xpath=ancestor::div[1]')
                if container.count() > 0:
                    # Get all text content and clean it up
                    full_text = container.first.inner_text(timeout=2000)
                    # Extract value by removing the label prefix
                    if full_text.startswith(label_text):
                        value = full_text[len(label_text):].strip()
                        # Remove common separators
                        value = value.lstrip(':').lstrip('-').strip()
                        if value:
                            result[field_name] = value
        except Exception:
            # Skip fields that can't be parsed
            continue

    return result


def scrape_sex_weight_fields(page, navigation) -> Dict[str, str]:
    """Scrape sex and weight related fields."""
    result = {}

    sex_weight_fields = {
        "Sex": "Sex",
        "Weight": "Weight",
        "Current Weight": "CurrentWeight",
        "Ideal Weight": "IdealWeight",
        "Weight Status": "WeightStatus",
    }

    for label_text, field_name in sex_weight_fields.items():
        try:
            label_locator = page.locator(f'text="{label_text}"')
            if label_locator.count() > 0:
                container = label_locator.first.locator('xpath=ancestor::div[1]')
                if container.count() > 0:
                    full_text = container.first.inner_text(timeout=2000)
                    if full_text.startswith(label_text):
                        value = full_text[len(label_text):].strip().lstrip(':').lstrip('-').strip()
                        if value:
                            result[field_name] = value
        except Exception:
            continue

    return result


def scrape_size_age_fields(page, navigation) -> Dict[str, str]:
    """Scrape size and age related fields."""
    result = {}

    size_age_fields = {
        "Size": "Size",
        "Age": "Age",
        "Date of Birth": "DateOfBirth",
        "Age in Years": "AgeInYears",
        "Age in Months": "AgeInMonths",
    }

    for label_text, field_name in size_age_fields.items():
        try:
            label_locator = page.locator(f'text="{label_text}"')
            if label_locator.count() > 0:
                container = label_locator.first.locator('xpath=ancestor::div[1]')
                if container.count() > 0:
                    full_text = container.first.inner_text(timeout=2000)
                    if full_text.startswith(label_text):
                        value = full_text[len(label_text):].strip().lstrip(':').lstrip('-').strip()
                        if value:
                            result[field_name] = value
        except Exception:
            continue

    return result


def extract_age_panel(page, result: Dict[str, Any]) -> None:
    """Extract age information from dedicated age panel."""
    try:
        age_panel = page.locator('[data-testid="age-panel"], .age-panel, #age-panel')
        if age_panel.count() > 0:
            age_text = age_panel.first.inner_text(timeout=2000).strip()
            if age_text:
                result["AgeInfo"] = age_text
    except Exception:
        pass


def _extract_header_profile_block(page, result: Dict[str, Any]) -> None:
    """Extract header/basic profile block fields."""
    try:
        # Name: "King Smash 13235"
        name_xpath = "//div[.//img[@id='animal-photo']]//h2[contains(@class,'font-semibold')]"
        name_elem = page.locator(f"xpath={name_xpath}")
        if name_elem.count() > 0:
            result["Name"] = name_elem.first.inner_text(timeout=1000).strip()

        # Muttville Animal ID: "MVSF-A-56233"
        id_xpath = "//div[.//img[@id='animal-photo']]//p[@class='text-[20px] text-gray-600']"
        id_elem = page.locator(f"xpath={id_xpath}")
        if id_elem.count() > 0:
            result["ID"] = id_elem.first.inner_text(timeout=1000).strip()

        # Labeled header fields
        header_labels = {
            "Species": "Species",
            "Breed": "Breed",
            "Color": "Color",
            "Pattern": "Pattern",
            "Sex": "Gender",
            "Altered": "AlteredBeforeArrival",  # May need to distinguish before/in care
            "DOB": "EstBirthdate",
            "Age (Y/M/D)": "AgeGroup",
        }

        for label, field in header_labels.items():
            try:
                value_xpath = f"//p[@class='col-span-1 font-bold' and normalize-space()='{label}']/following-sibling::p[1]"
                value_elem = page.locator(f"xpath={value_xpath}")
                if value_elem.count() > 0:
                    value = value_elem.first.inner_text(timeout=1000).strip()
                    if value:
                        result[field] = value
            except Exception:
                continue

        # Microchip # (under header)
        microchip_xpath = "//p[@class='col-span-1 font-bold' and normalize-space()='Microchip #']/following-sibling::ul[1]/li/text()"
        microchip_elem = page.locator(f"xpath={microchip_xpath}")
        if microchip_elem.count() > 0:
            result["MicrochipNumber"] = microchip_elem.first.inner_text(timeout=1000).strip()

        # Primary profile photo URL
        #
        # NOTE: We intentionally select the <img> element itself (no /@src) and
        # then read the "src" attribute. Using an XPath that returns the
        # @src attribute node and then calling get_attribute('src') would
        # always return None in Playwright, which silently produced an empty
        # Photos array in Firestore even though images rendered in ShelterLuv.
        photo_xpath = "//img[@id='animal-photo']"
        photo_elem = page.locator(f"xpath={photo_xpath}")
        if photo_elem.count() > 0:
            photo_url = photo_elem.first.get_attribute("src", timeout=1000)
            if photo_url:
                result["Photos"].append(photo_url)

    except Exception as e:
        print(f"Error extracting header profile block: {e}")


def _extract_status_from_page(page, result: Dict[str, Any]) -> None:
    """Extract Status from the page content using robust text search - critical for schema validation."""
    try:
        # Get some page content for debugging
        page_text = page.inner_text('body').lower()

        # Check for "Adopted" status (most specific)
        if 'adopted' in page_text:
            result["Status"] = "ADOPTED"
            return

        # Check for "Available for Adoption" (common for in-custody dogs)
        if 'available for adoption' in page_text:
            result["Status"] = "AVAILABLE"
            return

        # Check for "Pending" status
        if 'pending' in page_text:
            result["Status"] = "PENDING"
            return

        # Check for "Hold" status
        if 'hold' in page_text:
            result["Status"] = "HOLD"
            return

        # If no specific status found, default to AVAILABLE (since we're scraping in-custody view)
        result["Status"] = "AVAILABLE"

    except Exception as e:
        # If extraction fails, always set a default valid status
        result["Status"] = "AVAILABLE"

    # Debug logging for specific failing dogs
    internal_id = result.get("Internal-ID", "unknown")
    if internal_id in ["212174603", "211210850"]:
        print(f"🐛 DEBUG Status for dog {internal_id}: '{result.get('Status', 'MISSING')}' (page content sample: {page_text[:100]}...)")

def _extract_case_manager_from_categories(page, result: Dict[str, Any]) -> None:
    """Extract CaseManager from Categories table in History section.

    CaseManager is stored in the Categories table where Category Type = 'Adoption'
    and the 'New Value' column contains the case manager name.
    """
    try:
        # Find the Categories table in the History section
        # The Categories table comes after the h4 header with text "Categories"
        categories_table_xpath = "//h1[normalize-space()='History']/following::h4[contains(text(),'Categories')]/following::table[1]"
        categories_table = page.locator(f"xpath={categories_table_xpath}")

        if categories_table.count() == 0:
            # Try alternative: look for any table with Categories header nearby
            alt_xpath = "//h4[contains(text(),'Categories')]/following::table[1]"
            categories_table = page.locator(f"xpath={alt_xpath}")
            if categories_table.count() == 0:
                return

        # Get all rows from the table
        rows = categories_table.locator("tbody tr")

        # Look for rows where Category Type = "Adoption"
        for i in range(rows.count()):
            try:
                row = rows.nth(i)
                cells = row.locator("td")

                # Check if we have enough cells (should have 5: Date, Category Type, Previous Value, New Value, User)
                if cells.count() < 4:
                    continue

                # Get Category Type (2nd column, index 1)
                category_type = cells.nth(1).inner_text(timeout=1000).strip()

                # If this is an Adoption category, extract the New Value as CaseManager
                if category_type == "Adoption":
                    new_value = cells.nth(3).inner_text(timeout=1000).strip()  # 4th column (index 3)
                    if new_value and new_value.lower() != "none":
                        result["CaseManager"] = new_value
                        # Use the most recent Adoption category entry (first match in table)
                        break
            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting case manager from categories: {e}")

"""
Overview field parsing functions for ShelterLuv scraper.
Handles basic profile fields like species, color, age, weight, etc.
"""

from typing import Any, Dict

from .navigation import SELECTORS


def scrape_overview_fields(page, navigation) -> Dict[str, str]:
    """Scrape overview section fields using robust XPath selectors."""
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
            # Use robust XPath selector: find fieldset with label, then get button/input/textarea content
            xpath_selector = f'//fieldset[label[normalize-space()="{label_text}"]]//button | //fieldset[label[normalize-space()="{label_text}"]]//input'

            elements = page.locator(f"xpath={xpath_selector}")
            if elements.count() > 0:
                # Get text from first matching element
                value = elements.first.inner_text(timeout=1000).strip()
                if value:
                    result[field_name] = value
        except Exception:
            continue

    return result


def scrape_microchip_fields(page, navigation) -> Dict[str, str]:
    """Scrape microchip section using robust XPath selectors."""
    result = {}

    # Field mappings: label text -> schema field name
    field_mappings = {
        "Microchip Number": "MicrochipNumber",
        "Microchip Issuer": "MicrochipIssuer",
        "Implant Date": "MicrochipImplantDate",
    }

    for label_text, field_name in field_mappings.items():
        try:
            # Use robust XPath selector: find fieldset with label, then get button/input content
            xpath_selector = f'//fieldset[label[normalize-space()="{label_text}"]]//button | //fieldset[label[normalize-space()="{label_text}"]]//input'

            elements = page.locator(f"xpath={xpath_selector}")
            if elements.count() > 0:
                # Get text/value from first matching element
                if elements.first.locator("input").count() > 0:
                    value = elements.first.locator("input").get_attribute("value", timeout=1000)
                else:
                    value = elements.first.inner_text(timeout=1000).strip()

                if value:
                    result[field_name] = value
        except Exception:
            continue

    return result


def scrape_sex_weight_fields(page, navigation) -> Dict[str, str]:
    """Scrape sex and weight fields using robust XPath selectors, plus altered status."""
    result = {}

    # Field mappings: label text -> schema field name
    field_mappings = {
        "Sex": "Gender",  # Already handled by API, but keep for consistency
        "Weight": "Weight",  # Already handled by API, but keep for consistency
        "Altered Before Arrival": "AlteredBeforeArrival",
        "Altered In Care": "AlteredInCare",
    }

    for label_text, field_name in field_mappings.items():
        try:
            # Use robust XPath selector: find fieldset with label, then get button content
            xpath_selector = f'//fieldset[label[normalize-space()="{label_text}"]]//button'

            elements = page.locator(f"xpath={xpath_selector}")
            if elements.count() > 0:
                # Get text from first matching element
                value = elements.first.inner_text(timeout=1000).strip()
                if value:
                    result[field_name] = value
        except Exception:
            continue

    return result


def scrape_size_age_fields(page, navigation) -> Dict[str, str]:
    """Scrape size group, age group, and estimated birthdate using robust XPath selectors."""
    result = {}

    # Field mappings: label text -> schema field name
    field_mappings = {
        "Size Group": "Size",  # Map to existing Size field
        "Age Group": "AgeGroup",
        "Est. Birthdate": "EstBirthdate",
        "Estimated Birthdate": "EstBirthdate",
    }

    for label_text, field_name in field_mappings.items():
        try:
            # Use robust XPath selector: find fieldset with label, then get button content
            xpath_selector = f'//fieldset[label[normalize-space()="{label_text}"]]//button'

            elements = page.locator(f"xpath={xpath_selector}")
            if elements.count() > 0:
                # Get text from first matching element
                value = elements.first.inner_text(timeout=1000).strip()
                if value:
                    result[field_name] = value
        except Exception:
            continue

    return result


def scrape_intake_outcome_fields(page, navigation) -> Dict[str, str]:
    """Scrape intake/outcome fields using robust XPath selectors."""
    result = {}

    # Field mappings: label text -> schema field name
    field_mappings = {
        "Intake Type": "IntakeType",
        "Intake Date": "IntakeDate",
        "Intake Subtype": "IntakeSubtype",
        "Outcome Type": "OutcomeType",
        "Outcome Date": "OutcomeDate",
        "Outcome Subtype": "OutcomeSubtype",
        "Asilomar Intake": "AsilomarIntake",
        "Asilomar Outcome": "AsilomarOutcome",
        "Condition at Intake": "ConditionAtIntake",
        "Intake Jurisdiction": "JurisdictionIntake",
        "Outcome Jurisdiction": "JurisdictionOutcome",
        "Rabies Tag Number": "RabiesTagNumber",
        "Previous Shelter ID": "PreviousShelterId",
        "Previous Shelter Type": "PreviousShelterType",
        "Previous Shelter Issuer": "PreviousShelterIssuer",
    }

    for label_text, field_name in field_mappings.items():
        try:
            # Use robust XPath selector: find fieldset with label, then get button content
            xpath_selector = f'//fieldset[label[normalize-space()="{label_text}"]]//button'

            elements = page.locator(f"xpath={xpath_selector}")
            if elements.count() > 0:
                # Get text from first matching element
                value = elements.first.inner_text(timeout=1000).strip()
                if value:
                    result[field_name] = value
        except Exception:
            continue

    return result


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

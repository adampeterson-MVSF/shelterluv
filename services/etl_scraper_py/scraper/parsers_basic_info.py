"""
Basic information parsing functions for ShelterLuv scraper.

Handles extraction of fundamental animal information like microchip,
weight, and basic profile data.
"""

from typing import Any, Dict

from .navigation import SELECTORS
from .parsers_fields import extract_text_by_selector, extract_text_by_selectors, normalize_weight_string, extract_table_rows_by_xpath


def _extract_microchip_info(page, result: Dict[str, Any]) -> None:
    """Extract microchip information from the page."""
    try:
        # Microchip number
        microchip_selectors = [
            SELECTORS.microchip_number,
            ".microchip-number",
            "[data-microchip]",
            ".chip-number"
        ]
        result["MicrochipNumber"] = extract_text_by_selectors(page, microchip_selectors, "")

        # Microchip issuer
        issuer_selectors = [
            SELECTORS.microchip_issuer,
            ".microchip-issuer",
            ".chip-issuer"
        ]
        result["MicrochipIssuer"] = extract_text_by_selectors(page, issuer_selectors, "")

        # Microchip implant date
        implant_selectors = [
            SELECTORS.microchip_implant_date,
            ".microchip-implant-date",
            ".chip-implant-date"
        ]
        result["MicrochipImplantDate"] = extract_text_by_selectors(page, implant_selectors, "")

    except Exception as e:
        print(f"Error extracting microchip info: {e}")


def _extract_weight_info(page, result: Dict[str, Any]) -> None:
    """Extract weight information and normalize it."""
    try:
        weight_selectors = [
            SELECTORS.weight,
            ".weight",
            ".animal-weight",
            "[data-weight]"
        ]
        weight_text = extract_text_by_selectors(page, weight_selectors, "")

        if weight_text:
            weight_lbs, original = normalize_weight_string(weight_text)
            result["Weight"] = weight_lbs if weight_lbs is not None else weight_text

    except Exception as e:
        print(f"Error extracting weight info: {e}")


def _extract_previous_shelter_info(page, result: Dict[str, Any]) -> None:
    """Extract previous shelter information."""
    try:
        # Previous shelter ID
        prev_id_selectors = [
            SELECTORS.previous_shelter_id,
            ".previous-shelter-id",
            ".prev-shelter-id"
        ]
        result["PreviousShelterId"] = extract_text_by_selectors(page, prev_id_selectors, "")

        # Previous shelter type
        prev_type_selectors = [
            SELECTORS.previous_shelter_type,
            ".previous-shelter-type",
            ".prev-shelter-type"
        ]
        result["PreviousShelterType"] = extract_text_by_selectors(page, prev_type_selectors, "")

        # Previous shelter issuer
        prev_issuer_selectors = [
            SELECTORS.previous_shelter_issuer,
            ".previous-shelter-issuer",
            ".prev-shelter-issuer"
        ]
        result["PreviousShelterIssuer"] = extract_text_by_selectors(page, prev_issuer_selectors, "")

    except Exception as e:
        print(f"Error extracting previous shelter info: {e}")


def _extract_age_panel(page, result: Dict[str, Any]) -> None:
    """Extract age-related information from the age panel."""
    try:
        # Look for age information in various formats
        age_selectors = [
            ".age-display",
            "[data-age]",
            ".animal-age"
        ]

        for selector in age_selectors:
            try:
                age_elem = page.locator(selector)
                if age_elem.count() > 0:
                    age_text = age_elem.first.inner_text(timeout=1000).strip()
                    if age_text:
                        # Try to extract numeric age
                        import re
                        age_match = re.search(r'(\d+(?:\.\d+)?)\s*years?', age_text, re.IGNORECASE)
                        if age_match:
                            result["AgeYears"] = float(age_match.group(1))

                            # Generate display string
                            years = int(float(age_match.group(1)))
                            months = int((float(age_match.group(1)) - years) * 12)
                            if months == 0:
                                result["AgeDisplay"] = f"{years} year{'s' if years != 1 else ''}"
                            else:
                                result["AgeDisplay"] = f"{years} year{'s' if years != 1 else ''} {months} month{'s' if months != 1 else ''}"
                        else:
                            result["AgeDisplay"] = age_text
                        break
            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting age panel: {e}")


def _extract_microchip_info_from_medical_history(page, result: Dict[str, Any]) -> None:
    """Extract microchip information from ID Numbers table in medical history."""
    try:
        microchip_xpath = "//h1[normalize-space()='Complete Medical History']/following::h2[normalize-space()='ID Numbers']/following::table[1]"
        rows = extract_table_rows_by_xpath(page, microchip_xpath, min_cols=3, max_rows=5)

        if rows:
            # First row should contain microchip data
            first_row = rows[0]
            if len(first_row) >= 3:
                result["MicrochipNumber"] = first_row[0]
                result["MicrochipImplantDate"] = first_row[1]
                result["MicrochipIssuer"] = first_row[2]

    except Exception as e:
        print(f"Error extracting microchip info from medical history: {e}")


def _extract_previous_shelter_info_from_medical_history(page, result: Dict[str, Any]) -> None:
    """Extract previous shelter information from ID Numbers table in medical history."""
    try:
        prev_shelter_xpath = "//h1[normalize-space()='Complete Medical History']/following::h2[normalize-space()='ID Numbers']/following::table[2]"
        rows = extract_table_rows_by_xpath(page, prev_shelter_xpath, min_cols=3, max_rows=5)

        if rows:
            # First row should contain previous shelter data
            first_row = rows[0]
            if len(first_row) >= 3:
                result["PreviousShelterId"] = first_row[0]
                result["PreviousShelterType"] = first_row[1]
                result["PreviousShelterIssuer"] = first_row[2]

    except Exception as e:
        print(f"Error extracting previous shelter info from medical history: {e}")


def _extract_weight_info_from_medical_history(page, result: Dict[str, Any]) -> None:
    """Extract current weight from Weight table in medical history."""
    try:
        weight_xpath = "//h1[normalize-space()='Complete Medical History']/following::h2[normalize-space()='Weight']/following::table[1]"
        rows = extract_table_rows_by_xpath(page, weight_xpath, min_cols=2, max_rows=5)

        if rows:
            # First row should contain current weight
            first_row = rows[0]
            if len(first_row) >= 1 and first_row[0]:
                weight_text = first_row[0]
                weight_lbs, original = normalize_weight_string(weight_text)
                result["Weight"] = weight_lbs if weight_lbs is not None else weight_text

    except Exception as e:
        print(f"Error extracting weight info from medical history: {e}")
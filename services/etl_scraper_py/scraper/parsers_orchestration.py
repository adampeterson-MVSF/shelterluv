"""
Orchestration and utility parsing functions for ShelterLuv scraper.

Contains the main comprehensive record extraction function and utility functions
that coordinate parsing across multiple domains.
"""

from typing import Any, Dict

# Import all the domain-specific parsers
from .parsers_profile import scrape_overview_fields, scrape_sex_weight_fields, scrape_size_age_fields
from .parsers_history import (
    scrape_intake_outcome_fields,
    extract_event_history,
    extract_weight_history,
    extract_category_history,
    extract_compatibility_warnings,
    extract_attached_documents
)
from .parsers_basic_info import _extract_age_panel
from .parsers_profile import (
    _extract_header_profile_block, _extract_status_from_page, _extract_case_manager_from_categories
)
from .parsers_media import _extract_photos_documents
from .parsers_attributes import _extract_attributes_disclaimers, _derive_categories_from_attributes
from .parsers_memos import _extract_memos_section
from .parsers_medical_history import _extract_medical_history
from .parsers_behavior import extract_behavioral_assessments


def scrape_animal_record_summary_comprehensive(page, internal_id: str) -> Dict[str, Any]:
    """
    Comprehensive XPath-based scraper for ShelterLuv animal record summary page.
    Uses text-anchored selectors for robust extraction of all fields.

    URL: https://new.shelterluv.com/animals/documents/animal-record-summary?animals={internal_id}
    """
    result: Dict[str, Any] = {
        # Basic profile
        "Name": "",
        "ID": "",  # Muttville Animal ID
        "Species": "",
        "Breed": "",
        "Color": "",
        "Pattern": "",
        "DistinguishingMarks": "",
        "Gender": "",
        "AlteredBeforeArrival": "",
        "AlteredInCare": "",
        "AgeGroup": "",
        "EstBirthdate": "",
        "Size": "",
        "Weight": "",
        "Status": "",
        "MicrochipNumber": "",
        "MicrochipIssuer": "",
        "MicrochipImplantDate": "",
        "AdoptionPrice": "",
        "IntakeType": "",
        "IntakeSubtype": "",
        "OutcomeType": "",
        "OutcomeSubtype": "",
        "AsilomarIntake": "",
        "AsilomarOutcome": "",
        "ConditionAtIntake": "",
        "JurisdictionIntake": "",
        "JurisdictionOutcome": "",
        "RabiesTagNumber": "",
        "PreviousShelterId": "",
        "PreviousShelterType": "",
        "PreviousShelterIssuer": "",
        # Photos and documents
        "Photos": [],
        "Files": [],
        # Attributes
        "Attributes": [],
        "BehavioralAttributes": [],
        "PhysicalAttributes": [],
        # Memos
        "MemosRawHTML": "",
    }

    try:
        # 1. Extract header/basic profile information
        _extract_header_profile_block(page, result)

        # 2. Extract status (critical for schema validation)
        _extract_status_from_page(page, result)

        # 3. Extract photos and documents
        _extract_photos_documents(page, result)

        # 4. Extract attributes and disclaimers
        _extract_attributes_disclaimers(page, result)

        # 5. Extract memos section
        _extract_memos_section(page, result)

        # 6. Extract medical history (comprehensive)
        _extract_medical_history(page, result)

        # 7. Extract age panel information
        _extract_age_panel(page, result)

        # 8. Extract case manager from categories
        _extract_case_manager_from_categories(page, result)

        # 9. Derive additional categories from attributes
        _derive_categories_from_attributes(result)

        # 10. Extract comprehensive history data
        result["EventHistory"] = extract_event_history(page)
        result["WeightHistory"] = extract_weight_history(page)
        result["CategoryHistory"] = extract_category_history(page)

        # 11. Extract compatibility warnings from disclaimers
        result["CompatibilityWarnings"] = extract_compatibility_warnings(page)

        # 12. Extract attached documents
        result["AttachedDocuments"] = extract_attached_documents(page)

        # 13. Extract behavioral assessments
        result["BehavioralAssessments"] = extract_behavioral_assessments(page)

        return result

    except Exception as e:
        print(f"Error in comprehensive animal record extraction for {internal_id}: {e}")
        # Return partial result even on error
        return result


def scrape_memos_page(page, internal_id: str) -> str:
    """
    Scrape the memos/documents page for raw HTML content.
    This is a dedicated page for memos, different from the profile memos tab.
    """
    try:
        # Try to find the main content area
        content_selectors = [
            "[data-testid*='memos-content']",
            ".memos-content",
            "#memos-content",
            "main",
            ".content",
            "body"
        ]

        for selector in content_selectors:
            try:
                content = page.locator(selector).first
                if content.count() > 0:
                    html = content.inner_html(timeout=5000)
                    if html and len(html) > 100:  # Substantial content
                        return html
            except Exception:
                continue

        # Fallback: get the entire page HTML (not ideal but better than nothing)
        try:
            return page.inner_html(timeout=5000)
        except Exception:
            return ""

    except Exception as e:
        print(f"Error scraping memos page for {internal_id}: {e}")
        return ""

"""
Medical field parsing functions for ShelterLuv scraper.
Handles medical tabs, diagnoses, treatments, vaccinations, etc.
Prefers structured data, falls back to HTML parsing.
"""

from typing import Any, Dict

from .navigation import SELECTORS
from .parsers_basic_info import _extract_age_panel, _extract_microchip_info, _extract_weight_info, _extract_previous_shelter_info
from .parsers_medical_history import _extract_medical_history


def parse_medical_from_raw_record(raw_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract medical information from a canonical raw animal record.

    Args:
        raw_record: Canonical raw animal record with structured medical data.

    Returns:
        Dict with medical fields like MedicalSummary, MedicalDiagnoses, etc.
    """
    # For now, this is a placeholder - medical data often comes from tab scraping
    # rather than being part of the initial record structure
    return {}


def scrape_medical_fields(navigation) -> Dict[str, str]:
    """Scrape medical tab data."""
    result: Dict[str, str] = {}
    medical_tab = SELECTORS["tabs"]["medical"]  # type: ignore
    if not navigation._click_tab(medical_tab, timeout_ms=2000):
        return result

    subtabs = SELECTORS["subtabs"]["medical"]  # type: ignore
    result["MedicalSummary"] = navigation._extract_tab_text(subtabs["summary"])  # type: ignore
    result["MedicalDiagnoses"] = navigation._extract_tab_text(subtabs["diagnoses"])  # type: ignore
    result["MedicalDiagnosticTests"] = navigation._extract_tab_text(subtabs["diagnostic_tests"])  # type: ignore
    result["MedicalVaccines"] = navigation._extract_tab_text(subtabs["vaccines"])  # type: ignore
    result["MedicalDailyObservations"] = navigation._extract_tab_text(subtabs["daily_observations"])  # type: ignore
    result["MedicalPhysicalExams"] = navigation._extract_tab_text(subtabs["physical_exams"])  # type: ignore
    result["MedicalTreatments"] = navigation._extract_tab_text(subtabs["treatments"])  # type: ignore
    result["MedicalProcedures"] = navigation._extract_tab_text(subtabs["procedures"])  # type: ignore
    return result


def scrape_medical_history_from_comprehensive_page(page) -> Dict[str, Any]:
    """
    Extract complete medical history from the comprehensive medical history page.
    This is a comprehensive extraction that includes all medical data sections.
    """
    result = {}

    try:
        # Extract basic info
        _extract_microchip_info(page, result)
        _extract_previous_shelter_info(page, result)
        _extract_weight_info(page, result)

        # Extract complete medical history
        _extract_medical_history(page, result)

    except Exception as e:
        print(f"Error extracting medical history: {e}")

    return result

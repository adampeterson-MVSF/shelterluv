"""
Record summary parsing and orchestration for ShelterLuv scraper.

Handles high-level coordination of field parsers to build complete dog records.
"""

import logging
import re
from typing import Any, Dict

from .navigation import SELECTORS
from .parsers_categories import (
    parse_case_manager_from_adoption_category,
    parse_categories_from_text,
    scrape_categories_from_table,
)
from .parsers_behavior import scrape_behavioral_fields
from .parsers_medical import extract_medical_history
from .parsers_memos import parse_memos_by_type_pure
from .parsers_photos import scrape_attributes_from_page, scrape_files_table
from .parsers_orchestration import scrape_animal_record_summary_comprehensive
from .parsers_overview import scrape_microchip_fields
from .parsers_history import (
    scrape_history_fields,
    scrape_intake_outcome_fields,
    extract_case_manager_from_categories,
)
from .parsers_profile import (
    scrape_overview_fields,
    scrape_profile_main_content,
    scrape_sex_weight_fields,
    scrape_size_age_fields,
    extract_age_panel,
)

logger = logging.getLogger(__name__)


class ShelterLuvRecordSummaryParsers:
    """
    Record assembly orchestrator for ShelterLuv scraper.
    Coordinates field parsers to build complete dog records.
    """

    def __init__(self, page, navigation):
        self.page = page
        self.navigation = navigation

    def parse_memos_by_type(self, memos_html: str) -> Dict[str, str]:
        """
        Parse raw HTML memos into categorized notes by type.
        Returns dict with PersonalityNotes, IntakeNotes, MedicalNotes.
        Delegates to pure function.
        """
        return parse_memos_by_type_pure(memos_html)

    def _scrape_profile(self, animal_id: str) -> Dict[str, Any]:
        """
        Scrape the main animal profile page for categories and full profile text.
        Returns dict with AdoptionCategory, MedicalCategory, BehaviorCategory, FullAnimalProfile.
        Raises exception on failure.
        """
        url_main = f"https://new.shelterluv.com/animal/{animal_id}"
        self.page.goto(url_main, timeout=30000)
        self.page.wait_for_load_state("domcontentloaded")

        # Wait for profile tabs to become available
        try:
            tabs = SELECTORS["tabs"]
            tab_names_pattern = "|".join(
                [
                    tabs["profile"],
                    tabs["medical"],
                    tabs["history"],  # type: ignore
                    tabs["files"],
                    tabs["behavioral"],  # type: ignore
                ]
            )
            self.page.get_by_role("tab", name=re.compile(f"({tab_names_pattern})", re.I)).first.wait_for(timeout=10000)  # type: ignore
        except Exception:
            # Some profiles might have different layouts
            pass

        result: Dict[str, Any] = {
            "FullAnimalProfile": "",
            "AdoptionCategory": "",
            "MedicalCategory": "",
            "BehaviorCategory": "",
            "VolunteerCategory": "",
            # Behavioral
            "BehaviorPlan": "",
            "BehaviorAssessment": "",
            "BehaviorPlaygroups": "",
            "BehaviorChecks": "",
            # Medical
            "MedicalSummary": "",
            "MedicalDiagnoses": "",
            "MedicalDiagnosticTests": "",
            "MedicalVaccines": "",
            "MedicalDailyObservations": "",
            "MedicalPhysicalExams": "",
            "MedicalTreatments": "",
            "MedicalProcedures": "",
            # Attributes
            "Attributes": [],
            # Files table
            "Files": [],
            # History subtables (raw rows)
            "HistoryIntakesOutcomes": [],
            "HistoryCaretakers": [],
            "HistoryStatuses": [],
            "HistoryLocations": [],
            "HistoryProfileEdits": [],
            # Memos (from profile Memos tab)
            "MemosLatest": [],
            "MemosMedical": [],
        }

        # Try structured categories first (History > Categories)
        navigated_categories = False
        history_tab = SELECTORS["tabs"]["history"]  # type: ignore
        categories_tab = SELECTORS["tabs"]["categories"]  # type: ignore
        if self.navigation._click_tab(history_tab, timeout_ms=2000):
            if self.navigation._click_tab(categories_tab, timeout_ms=2000):
                navigated_categories = True
                table = self.navigation._read_table_from_panel("Categories")
                structured_categories = scrape_categories_from_table(self.navigation, table)
                result.update(structured_categories)

        # Fall back to main content scraping
        main_content = scrape_profile_main_content(self.page)
        result["FullAnimalProfile"] = main_content
        if not navigated_categories or not any(
            result.get(cat)
            for cat in [
                "AdoptionCategory",
                "MedicalCategory",
                "BehaviorCategory",
                "VolunteerCategory",
            ]
        ):
            parsed_categories = parse_categories_from_text(main_content)
            result.update(parsed_categories)

        # Extract CaseManager from AdoptionCategory if available
        adoption_category = result.get("AdoptionCategory", "")
        if adoption_category:
            case_manager = parse_case_manager_from_adoption_category(adoption_category)
            if case_manager:
                result["CaseManager"] = case_manager

        # Scrape all other sections using field parsers
        behavioral_data = scrape_behavioral_fields(self.navigation)
        result.update(behavioral_data)

        medical_data = extract_medical_history(self.page, result)
        if medical_data:
            result.update(medical_data)

        attributes_data = scrape_attributes_from_page(self.page, self.navigation)
        # Ensure we have the correct data structure
        if (
            isinstance(attributes_data, dict)
            and "behavioral" in attributes_data
            and "physical" in attributes_data
        ):
            behavioral_attrs = attributes_data.get("behavioral", [])
            physical_attrs = attributes_data.get("physical", [])
            result["Attributes"] = (
                behavioral_attrs + physical_attrs
            )  # Combined for backward compatibility
            result["BehavioralAttributes"] = behavioral_attrs
            result["PhysicalAttributes"] = physical_attrs
        else:
            # Fallback if scraper returned unexpected format
            result["Attributes"] = []
            result["BehavioralAttributes"] = []
            result["PhysicalAttributes"] = []

        # Scrape new field-level data using robust XPath selectors
        overview_data = scrape_overview_fields(self.page, self.navigation)
        result.update(overview_data)

        microchip_data = scrape_microchip_fields(self.page, self.navigation)
        result.update(microchip_data)

        sex_weight_data = scrape_sex_weight_fields(self.page, self.navigation)
        result.update(sex_weight_data)

        size_age_data = scrape_size_age_fields(self.page, self.navigation)
        result.update(size_age_data)

        intake_outcome_data = scrape_intake_outcome_fields(self.page, self.navigation)
        result.update(intake_outcome_data)

        result["Files"] = scrape_files_table(self.navigation)

        history_data = scrape_history_fields(self.navigation)
        result.update(history_data)

        memos_data = parse_memos_by_type_pure("")  # Empty for profile-only scraping
        result.update(memos_data)

        return result

    def scrape_profile_only(self, animal_id: str) -> Dict[str, Any]:
        """
        Scrape only the main animal profile page (no memos page).
        Returns dict with profile data and all tabs, but no MemosRawHTML.
        Raises exception on failure.
        """
        return self._scrape_profile(animal_id)

    def scrape_full_details(self, animal_id: str, internal_id: str) -> Dict[str, Any]:
        """
        Scrape profile + memos page (full details for tooling/tests).
        Returns dict with profile data and MemosRawHTML.
        Raises exception on failure.
        """
        result = self._scrape_profile(animal_id)
        try:
            memos_html = self._scrape_memos_page(internal_id)
            result["MemosRawHTML"] = memos_html
            # Parse memos into categorized notes
            memos_data = parse_memos_by_type_pure(memos_html)
            result.update(memos_data)
        except Exception as e:
            result["ScrapeError"] = str(e)
        return result

    def scrape_animal_record_summary(self, animal_id: str, internal_id: str) -> Dict[str, Any]:
        """
        Scrape the animal profile page which contains comprehensive data including foster information.
        This page provides all animal information including dynamic content like foster details.
        URL: https://new.shelterluv.com/animal/{animal_id}

        Uses the new comprehensive XPath-based scraper for robust extraction.
        """
        url = f"https://new.shelterluv.com/animal/{animal_id}"
        self.page.goto(url, timeout=30000)
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2000)  # Wait for initial load
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(3000)  # Extra time for Livewire components

        # Use the comprehensive XPath-based scraper
        try:
            result = scrape_animal_record_summary_comprehensive(self.page, internal_id)
            logger.debug(f"Comprehensive scraper succeeded for dog {internal_id}")
        except Exception as e:
            # Fallback to minimal result if comprehensive scraper fails
            logger.warning(f"Comprehensive scraper failed for dog {internal_id}, using fallback: {e}")
            result = {
                "Internal-ID": internal_id,
                "ID": animal_id,
                "Status": "AVAILABLE",
                "Name": "",
            }

        # Ensure required IDs are set
        result["Internal-ID"] = internal_id
        result["ID"] = animal_id

        return result

    def scrape_dog_details(self, animal_id: str, internal_id: str) -> Dict[str, Any]:
        """
        Scrapes all required data for a single dog using the animal record summary page.
        This provides comprehensive data from a single page load.
        """
        return self.scrape_animal_record_summary(animal_id, internal_id)

    def _scrape_memos_page(self, internal_id: str) -> str:
        """Scrape the memos page for raw HTML content."""
        url_memos = f"https://new.shelterluv.com/animals/documents/memos?animals={internal_id}"
        self.page.goto(url_memos, timeout=30000)
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1000)  # Wait for dynamic content

        # Extract memos HTML
        memos_html = self.page.locator("body").inner_html()
        return memos_html

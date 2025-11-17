"""
Data parsing and extraction for ShelterLuv scraper.

Handles extraction of structured data from scraped HTML content.
Pure memo parsing functions and record assembly orchestrator.
"""

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

from .navigation import SELECTORS
from .parsers_categories import (
    parse_case_manager_from_adoption_category,
    parse_categories_from_text,
    scrape_categories_from_table,
)
from .parsers_behavior import scrape_behavioral_fields
from .parsers_medical import scrape_medical_fields
from .parsers_photos import scrape_attributes_from_page, scrape_files_table
from .parsers_orchestration import scrape_animal_record_summary_comprehensive
from .parsers_overview import scrape_microchip_fields
from .parsers_history import (
    scrape_history_fields,
    scrape_intake_outcome_fields,
    extract_case_manager_from_categories,
)
from .parsers_memos import (
    scrape_memos_from_profile,
    scrape_memos_page,
    extract_memos_section,
)
from .parsers_profile import (
    scrape_overview_fields,
    scrape_profile_main_content,
    scrape_sex_weight_fields,
    scrape_size_age_fields,
    extract_age_panel,
)

# Keyword sets for memo categorization (pattern-driven)
PERSONALITY_KEYWORDS = [
    "personality",
    "behavior",
    "temperament",
    "disposition",
    "playful",
    "friendly",
    "shy",
    "aggressive",
    "social",
    "anxious",
    "calm",
    "energy",
]

INTAKE_KEYWORDS = [
    "intake",
    "background",
    "history",
    "came from",
    "owner surrender",
    "stray",
    "rescued",
    "previous",
    "origin",
]

MEDICAL_KEYWORDS = [
    "medical",
    "health",
    "vet",
    "treatment",
    "medication",
    "surgery",
    "vaccine",
    "illness",
    "condition",
    "diagnosis",
    "exam",
    "test",
]


def parse_memos_by_type_pure(memos_html: str) -> Dict[str, str]:
    """
    Parse raw HTML memos into categorized notes by type.
    Returns dict with PersonalityNotes, IntakeNotes, MedicalNotes.

    Pure function that wires together clean_memo_html, split_memo_into_sections,
    and categorize_section building blocks.
    
    Also recognizes "Kennel Card / Website Memo" headers and categorizes them as personality notes.
    """
    text = clean_memo_html(memos_html)
    sections = split_memo_into_sections(text)

    personality_sections = []
    intake_sections = []
    medical_sections = []

    for section in sections:
        section_clean = section.strip()
        if not section_clean or len(section_clean) < 10:  # Skip empty/short sections
            continue

        # Check for "Kennel Card / Website Memo" header - always categorize as personality
        section_lower = section_clean.lower()
        if "kennel card" in section_lower or "website memo" in section_lower:
            # Extract content after the header
            lines = section_clean.split("\n")
            content_lines = []
            found_header = False
            for line in lines:
                if "kennel card" in line.lower() or "website memo" in line.lower():
                    found_header = True
                    # Skip the header line itself, but include content after it
                    continue
                if found_header or not any(keyword in line.lower() for keyword in ["kennel card", "website memo"]):
                    content_lines.append(line)
            
            if content_lines:
                content = "\n".join(content_lines).strip()
                if content:
                    personality_sections.append(content)
            continue

        # Categorize section by type
        section_type = categorize_section(section_clean)
        if section_type == "medical":
            medical_sections.append(section_clean)
        elif section_type == "intake":
            intake_sections.append(section_clean)
        elif section_type == "personality":
            personality_sections.append(section_clean)

    return {
        "PersonalityNotes": "\n\n".join(personality_sections) if personality_sections else "Not Available",
        "IntakeNotes": "\n\n".join(intake_sections) if intake_sections else "",
        "MedicalNotes": "\n\n".join(medical_sections) if medical_sections else "Not Available",
    }


def clean_memo_html(html: str) -> str:
    """Clean HTML from memo content, preserving line breaks."""
    from html import unescape

    # Strip HTML tags but preserve line breaks
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return unescape(text)


def split_memo_into_sections(clean_html: str) -> List[str]:
    """Split memo text into sections by timestamps and headers."""
    # Split on timestamps, double newlines, or explicit headers
    sections = re.split(r"\n\s*\n|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}", clean_html)

    # If no sections created, treat entire text as one section
    if not sections or (len(sections) == 1 and not sections[0].strip()):
        sections = [clean_html]

    return sections


def categorize_section(section: str) -> str:
    """
    Categorize a memo section by keyword matching.
    Returns 'medical', 'intake', 'personality', or empty string.

    Priority: medical > intake > personality (medical has highest priority)
    """
    section_lower = section.lower().strip()

    # Get keyword counts for each category
    medical_count = _count_keywords_pure(section_lower, MEDICAL_KEYWORDS)
    intake_count = _count_keywords_pure(section_lower, INTAKE_KEYWORDS)
    personality_count = _count_keywords_pure(section_lower, PERSONALITY_KEYWORDS)

    # Return category with most matches (ties: medical > intake > personality)
    if medical_count > 0 and medical_count >= intake_count and medical_count >= personality_count:
        return "medical"
    elif intake_count > 0 and intake_count >= personality_count:
        return "intake"
    elif personality_count > 0:
        return "personality"

    return ""


# Backward compatibility: keep old function names that delegate to new ones
def _clean_memo_html_pure(memos_html: str) -> str:
    """Backward compatibility wrapper."""
    return clean_memo_html(memos_html)


def _split_memo_into_sections_pure(text: str) -> List[str]:
    """Backward compatibility wrapper."""
    return split_memo_into_sections(text)


def _categorize_memo_section_pure(section_lower: str) -> str:
    """Backward compatibility wrapper."""
    return categorize_section(section_lower)


def _count_keywords_pure(text: str, keywords: List[str]) -> int:
    """Count how many keywords appear in text."""
    return sum(1 for keyword in keywords if keyword in text)


class ShelterLuvParsers:
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
        behavioral_data = scrape_behavioral_fields(self.page, self.navigation)
        result.update(behavioral_data)

        medical_data = scrape_medical_fields(self.navigation)
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

        memos_data = scrape_memos_from_profile(self.page, self.navigation)
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
            memos_html = scrape_memos_page(self.page, internal_id)
            result["MemosRawHTML"] = memos_html
        except Exception as e:
            result["ScrapeError"] = str(e)
        return result

    def scrape_animal_record_summary(self, animal_id: str, internal_id: str) -> Dict[str, Any]:
        """
        Scrape the animal record summary page which contains comprehensive data.
        This page provides all animal information in a single, well-structured document.
        URL: https://new.shelterluv.com/animals/documents/animal-record-summary?animals={internal_id}

        Uses the new comprehensive XPath-based scraper for robust extraction.
        """
        url = f"https://new.shelterluv.com/animals/documents/animal-record-summary?animals={internal_id}"
        self.page.goto(url, timeout=30000)
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(2000)  # Wait for dynamic content

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

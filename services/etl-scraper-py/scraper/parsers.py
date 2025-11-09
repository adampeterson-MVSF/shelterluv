"""
Data parsing and extraction for ShelterLuv scraper.

Handles extraction of structured data from scraped HTML content.
"""

from typing import Dict, Any, List, Tuple
import re
from .navigation import SELECTORS

# Mapping from scraped category names to schema field names
CATEGORY_MAP = {
    "Adoption Category": "AdoptionCategory",
    "Medical Category": "MedicalCategory",
    "Behavior Category": "BehaviorCategory",
}


class ShelterLuvParsers:
    """
    Data parsing and extraction methods for ShelterLuv scraper.
    """

    def __init__(self, page, navigation):
        self.page = page
        self.navigation = navigation

    def _parse_categories(self, text: str) -> Dict[str, str]:
        """
        Parse category information from ShelterLuv profile text.
        Returns dict with AdoptionCategory, MedicalCategory, BehaviorCategory keys.
        """
        categories = {}
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line in CATEGORY_MAP:
                if i + 1 < len(lines):
                    categories[CATEGORY_MAP[line]] = lines[i + 1].strip()
        return categories

    def _scrape_profile_main_content(self) -> str:
        """Scrape the main profile content and extract categories."""
        main_content = self.page.locator(SELECTORS["case_manager_section"])
        if main_content.count() == 0:
            return ""

        full_text = main_content.first.inner_text(timeout=5000)
        return full_text.strip()

    def _scrape_profile_categories_structured(self) -> Dict[str, str]:
        """Scrape categories from structured table format."""
        categories = {}
        table = self.navigation._read_table_from_panel("Categories")
        headers = [h.lower() for h in table.get("headers", [])]
        rows = table.get("rows", [])

        if not rows:
            return categories

        # Find category and value column keys
        cat_key = None
        val_key = None
        for candidate in ["category", "name", "type"]:
            if candidate in headers:
                cat_key = candidate
                break
        for candidate in ["value", "status", "selection"]:
            if candidate in headers:
                val_key = candidate
                break

        latest_by_category: Dict[str, str] = {}
        for row in rows:
            if cat_key and val_key and cat_key in row and val_key in row:
                k = row[cat_key].strip()
                v = row[val_key].strip()
            else:
                # Fallback to first and last cell in the row
                if len(row) == 0:
                    continue
                ordered = [row[k] for k in sorted(row.keys(), key=lambda x: int(x) if x.isdigit() else 0)]
                k = ordered[0].strip()
                v = ordered[-1].strip()
            if k and v:
                latest_by_category[k] = v

        # Map into our schema keys
        if "Adoption Category" in latest_by_category:
            categories["AdoptionCategory"] = latest_by_category["Adoption Category"]
        if "Medical Category" in latest_by_category:
            categories["MedicalCategory"] = latest_by_category["Medical Category"]
        if "Behavior Category" in latest_by_category:
            categories["BehaviorCategory"] = latest_by_category["Behavior Category"]

        return categories

    def _scrape_behavioral_data(self, result: Dict[str, Any]) -> None:
        """Scrape behavioral tab data."""
        behavioral_tab = SELECTORS["tabs"]["behavioral"]
        if not self.navigation._click_tab(behavioral_tab, timeout_ms=2000):
            return

        subtabs = SELECTORS["subtabs"]["behavioral"]
        result["BehaviorPlan"] = self.navigation._extract_tab_text(subtabs["plan"])
        result["BehaviorAssessment"] = self.navigation._extract_tab_text(subtabs["assessment"])
        result["BehaviorPlaygroups"] = self.navigation._extract_tab_text(subtabs["playgroups"])
        result["BehaviorChecks"] = self.navigation._extract_tab_text(subtabs["behavior_checks"])

    def _scrape_medical_data(self, result: Dict[str, Any]) -> None:
        """Scrape medical tab data."""
        medical_tab = SELECTORS["tabs"]["medical"]
        if not self.navigation._click_tab(medical_tab, timeout_ms=2000):
            return

        subtabs = SELECTORS["subtabs"]["medical"]
        result["MedicalSummary"] = self.navigation._extract_tab_text(subtabs["summary"])
        result["MedicalDiagnoses"] = self.navigation._extract_tab_text(subtabs["diagnoses"])
        result["MedicalDiagnosticTests"] = self.navigation._extract_tab_text(subtabs["diagnostic_tests"])
        result["MedicalVaccines"] = self.navigation._extract_tab_text(subtabs["vaccines"])
        result["MedicalDailyObservations"] = self.navigation._extract_tab_text(subtabs["daily_observations"])
        result["MedicalPhysicalExams"] = self.navigation._extract_tab_text(subtabs["physical_exams"])
        result["MedicalTreatments"] = self.navigation._extract_tab_text(subtabs["treatments"])
        result["MedicalProcedures"] = self.navigation._extract_tab_text(subtabs["procedures"])

    def _scrape_attributes(self, result: Dict[str, Any]) -> None:
        """Scrape attributes (badges/chips)."""
        attributes_tab = SELECTORS["tabs"]["attributes"]
        if not self.navigation._click_tab(attributes_tab, timeout_ms=2000):
            return

        try:
            pills = self.page.locator(SELECTORS["attributes_badges"])
            count = pills.count()
            if count > 0:
                values = []
                for i in range(count):
                    txt = pills.nth(i).inner_text(timeout=1500).strip()
                    if txt:
                        values.append(txt)
                result["Attributes"] = values
        except Exception:
            pass

    def _scrape_files(self, result: Dict[str, Any]) -> None:
        """Scrape files table."""
        files_tab = SELECTORS["tabs"]["files"]
        if not self.navigation._click_tab(files_tab, timeout_ms=1500):
            return

        table = self.navigation._read_table_from_panel(files_tab)
        rows = table.get("rows", [])
        normalized = []
        for row in rows:
            item = {
                "Name": row.get("Name") or row.get("0") or "",
                "Type": row.get("Type") or row.get("1") or "",
                "DocumentDelivery": row.get("Document Delivery") or row.get("2") or "",
            }
            if any(v for v in item.values()):
                normalized.append(item)
        result["Files"] = normalized

    def _scrape_history_data(self, result: Dict[str, Any]) -> None:
        """Scrape history subtabs."""
        history_tab = SELECTORS["tabs"]["history"]
        if not self.navigation._click_tab(history_tab, timeout_ms=1500):
            return

        subtabs = SELECTORS["subtabs"]["history"]
        for subtab_key, key in [
            ("intakes_outcomes", "HistoryIntakesOutcomes"),
            ("caretakers", "HistoryCaretakers"),
            ("statuses", "HistoryStatuses"),
            ("locations", "HistoryLocations"),
            ("profile_edits", "HistoryProfileEdits"),
        ]:
            subtab_name = subtabs[subtab_key]
            if self.navigation._click_tab(subtab_name, timeout_ms=1200):
                table = self.navigation._read_table_from_panel(subtab_name)
                result[key] = table.get("rows", [])

    def _scrape_memos_from_profile(self, result: Dict[str, Any]) -> None:
        """Scrape memos from profile Memos tab."""
        memos_tab = SELECTORS["tabs"]["memos"]
        if not self.navigation._click_tab(memos_tab, timeout_ms=1500):
            return

        subtabs = SELECTORS["subtabs"]["memos"]
        for subtab_key, key in [("latest", "MemosLatest"), ("medical", "MemosMedical")]:
            subtab_name = subtabs[subtab_key]
            if self.navigation._click_tab(subtab_name, timeout_ms=1000):
                try:
                    panel = self.navigation._get_tabpanel(subtab_name)
                    items = panel.get_by_role("listitem")
                    count = items.count()
                    texts = []
                    for i in range(count):
                        t = items.nth(i).inner_text(timeout=1500).strip()
                        if t:
                            texts.append(t)
                    result[key] = texts
                except Exception:
                    pass

    def parse_memos_by_type(self, memos_html: str) -> Dict[str, str]:
        """
        Parse raw HTML memos into categorized notes by type.
        Returns dict with PersonalityNotes, IntakeNotes, MedicalNotes.

        Memo parsing is clearly split by type with small, focused functions.
        """
        text = self._clean_memo_html(memos_html)
        sections = self._split_memo_into_sections(text)

        personality_sections = []
        intake_sections = []
        medical_sections = []

        for section in sections:
            section_clean = section.strip()
            if not section_clean or len(section_clean) < 10:  # Skip empty/short sections
                continue

            # Categorize section by type
            section_type = self._categorize_memo_section(section_clean.lower())
            if section_type == 'medical':
                medical_sections.append(section_clean)
            elif section_type == 'intake':
                intake_sections.append(section_clean)
            elif section_type == 'personality':
                personality_sections.append(section_clean)

        return {
            'PersonalityNotes': '\n\n'.join(personality_sections) if personality_sections else '',
            'IntakeNotes': '\n\n'.join(intake_sections) if intake_sections else '',
            'MedicalNotes': '\n\n'.join(medical_sections) if medical_sections else ''
        }

    def _clean_memo_html(self, memos_html: str) -> str:
        """Clean HTML from memo content, preserving line breaks."""
        from html import unescape

        # Strip HTML tags but preserve line breaks
        text = re.sub(r'<br\s*/?>', '\n', memos_html, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        return unescape(text)

    def _split_memo_into_sections(self, text: str) -> List[str]:
        """Split memo text into sections by timestamps and headers."""
        # Split on timestamps, double newlines, or explicit headers
        sections = re.split(r'\n\s*\n|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}', text)

        # If no sections created, treat entire text as one section
        if not sections or (len(sections) == 1 and not sections[0].strip()):
            sections = [text]

        return sections

    def _categorize_memo_section(self, section_lower: str) -> str:
        """
        Categorize a memo section by keyword matching.
        Returns 'medical', 'intake', 'personality', or empty string.
        """
        # Get keyword counts for each category
        medical_count = self._count_keywords(section_lower, self._get_medical_keywords())
        intake_count = self._count_keywords(section_lower, self._get_intake_keywords())
        personality_count = self._count_keywords(section_lower, self._get_personality_keywords())

        # Return category with most matches (ties: medical > intake > personality)
        if medical_count > 0 and medical_count >= intake_count and medical_count >= personality_count:
            return 'medical'
        elif intake_count > 0 and intake_count >= personality_count:
            return 'intake'
        elif personality_count > 0:
            return 'personality'

        return ''

    def _count_keywords(self, text: str, keywords: List[str]) -> int:
        """Count how many keywords appear in text."""
        return sum(1 for keyword in keywords if keyword in text)

    def _get_personality_keywords(self) -> List[str]:
        """Get keywords for personality/behavior categorization."""
        return ['personality', 'behavior', 'temperament', 'disposition', 'playful',
                'friendly', 'shy', 'aggressive', 'social', 'anxious', 'calm', 'energy']

    def _get_intake_keywords(self) -> List[str]:
        """Get keywords for intake/background categorization."""
        return ['intake', 'background', 'history', 'came from', 'owner surrender',
                'stray', 'rescued', 'previous', 'origin']

    def _get_medical_keywords(self) -> List[str]:
        """Get keywords for medical/health categorization."""
        return ['medical', 'health', 'vet', 'treatment', 'medication', 'surgery',
                'vaccine', 'illness', 'condition', 'diagnosis', 'exam', 'test']

    def _scrape_profile(self, animal_id: str) -> Dict[str, Any]:
        """
        Scrape the main animal profile page for categories and full profile text.
        Returns dict with AdoptionCategory, MedicalCategory, BehaviorCategory, FullAnimalProfile.
        Raises exception on failure.
        """
        url_main = f"https://new.shelterluv.com/animal/{animal_id}"
        self.page.goto(url_main, timeout=10000)
        self.page.wait_for_load_state("domcontentloaded")

        # Wait for profile tabs to become available
        try:
            tabs = SELECTORS["tabs"]
            tab_names_pattern = "|".join([
                tabs["profile"], tabs["medical"], tabs["history"],
                tabs["files"], tabs["behavioral"]
            ])
            self.page.get_by_role("tab", name=re.compile(f"({tab_names_pattern})", re.I)).first.wait_for(timeout=10000)
        except Exception:
            # Some profiles might have different layouts
            pass

        result: Dict[str, Any] = {
            "FullAnimalProfile": "",
            "AdoptionCategory": "",
            "MedicalCategory": "",
            "BehaviorCategory": "",
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
            "MemosMedical": []
        }

        # Try structured categories first (History > Categories)
        navigated_categories = False
        history_tab = SELECTORS["tabs"]["history"]
        categories_tab = SELECTORS["tabs"]["categories"]
        if self.navigation._click_tab(history_tab, timeout_ms=2000):
            if self.navigation._click_tab(categories_tab, timeout_ms=2000):
                navigated_categories = True
                structured_categories = self._scrape_profile_categories_structured()
                result.update(structured_categories)

        # Fall back to main content scraping
        if not navigated_categories:
            main_content = self._scrape_profile_main_content()
            result["FullAnimalProfile"] = main_content
            parsed_categories = self._parse_categories(main_content)
            result.update(parsed_categories)
        else:
            # Even with structured categories, get main content for FullAnimalProfile
            main_content = self._scrape_profile_main_content()
            result["FullAnimalProfile"] = main_content

        # Scrape all other sections
        self._scrape_behavioral_data(result)
        self._scrape_medical_data(result)
        self._scrape_attributes(result)
        self._scrape_files(result)
        self._scrape_history_data(result)
        self._scrape_memos_from_profile(result)

        return result

    def _scrape_memos(self, internal_id: str) -> str:
        """
        Scrape the memos/documents page for raw HTML content.
        Returns memo text or empty string.
        Raises exception on failure.
        """
        url_memos = f"https://new.shelterluv.com/animals/documents/memos?animals={internal_id}"
        self.page.goto(url_memos, timeout=10000)

        for selector in SELECTORS["memo_selectors"]:
            memo_elements = self.page.locator(selector)
            if memo_elements.count() > 0:
                all_memos = []
                for i in range(memo_elements.count()):
                    memo_text = memo_elements.nth(i).inner_text(timeout=2000).strip()
                    if memo_text:
                        all_memos.append(memo_text)

                if all_memos:
                    return "\n\n".join(all_memos)

        # Fallback: try to get body text if no structured memos found
        page_text = self.page.locator('body').inner_text(timeout=3000)
        if any(keyword in page_text for keyword in ["Medical", "Intake", "Behavior"]):
            return page_text.strip()

        return ""

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
            memos_html = self._scrape_memos(internal_id)
            result["MemosRawHTML"] = memos_html
        except Exception as e:
            result["ScrapeError"] = str(e)
        return result

    def scrape_dog_details(self, animal_id: str, internal_id: str) -> Dict[str, Any]:
        """
        Scrapes all required data for a single dog (backwards compatibility).
        Returns normalized data structure with consistent keys.
        """
        return self.scrape_full_details(animal_id, internal_id)

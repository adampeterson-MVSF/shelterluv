"""
Navigation and UI interaction for ShelterLuv scraper.

Handles tab navigation, panel access, and table reading.
"""

import re
from typing import Any, Dict, List

# Navigation and table-related selectors
SELECTORS: Dict[str, Any] = {
    # Content anchors
    "case_manager_section": 'div:has-text("Case Manager")',
    # Generic memo content fallbacks (when no roles are available)
    "memo_selectors": ['div[class*="memo"]', ".memo-content", '[class*="memo"]', "pre", ".content"],
    # Tab names used throughout scraping
    "tabs": {
        "behavioral": "Behavioral",
        "medical": "Medical",
        "history": "History",
        "files": "Files",
        "attributes": "Attributes",
        "memos": "Memos",
        "categories": "Categories",
        "profile": "Profile",
    },
    # Sub-tabs within main tabs
    "subtabs": {
        "behavioral": {
            "plan": "Plan",
            "assessment": "Assessment",
            "playgroups": "Playgroups",
            "behavior_checks": "Behavior Checks",
        },
        "medical": {
            "summary": "Summary",
            "diagnoses": "Diagnoses",
            "diagnostic_tests": "Diagnostic Tests",
            "vaccines": "Vaccines",
            "daily_observations": "Daily Observations",
            "physical_exams": "Physical Exams",
            "treatments": "Treatments",
            "procedures": "Procedures/Surgeries",
        },
        "history": {
            "intakes_outcomes": "Intakes/Outcomes",
            "caretakers": "Caretakers",
            "statuses": "Statuses",
            "locations": "Locations",
            "profile_edits": "Profile Edits",
        },
        "memos": {"latest": "Latest", "medical": "Medical"},
    },
    # CSS selectors for elements that might change
    "attributes_badges": '[class*="badge" i], [class*="chip" i]',
    # Basic info selectors
    "microchip_number": ".microchip-number, [data-microchip], .chip-number",
    "microchip_issuer": ".microchip-issuer, .chip-issuer",
    "microchip_implant_date": ".microchip-implant-date, .chip-implant-date",
    "weight": ".weight, .animal-weight, [data-weight]",
    "previous_shelter_id": ".previous-shelter-id, .prev-shelter-id",
    "previous_shelter_type": ".previous-shelter-type, .prev-shelter-type",
    "previous_shelter_issuer": ".previous-shelter-issuer, .prev-shelter-issuer",
    # History selectors
    "history_section": "h1:has-text('History')",
    "weight_table": "h2:has-text('Weight')",
    "categories_table": "h4:has-text('Categories')",
    # Medical data table selectors
    "vaccination_table": ".vaccinations-table, .vaccination-history table",
    "treatments_due_table": ".treatments-due table, .due-treatments table",
    "treatment_history_table": ".treatment-history table, .treatment-records table",
    "active_diagnoses_table": ".active-diagnoses table, .current-diagnoses table",
    "resolved_diagnoses_table": ".resolved-diagnoses table, .past-diagnoses table",
    "diagnostic_tests_table": ".diagnostic-tests table, .lab-tests table",
    "physical_exams_table": ".physical-exams table, .exam-records table",
    "procedures_table": ".procedures-surgeries table, .surgical-procedures table",
    # ARIA roles used for table parsing
    "table_roles": {
        "columnheader": "columnheader",
        "row": "row",
        "cell": "cell",
        "gridcell": "gridcell",
        "tabpanel": "tabpanel",
    },
}


class ShelterLuvNavigation:
    """
    Navigation and UI interaction methods for ShelterLuv scraper.
    """

    def __init__(self, page):
        self.page = page

    def _click_tab(self, name: str, timeout_ms: int = 5000) -> bool:
        """Click a tab by accessible name."""
        try:
            self.page.get_by_role("tab", name=name).first.click(timeout=timeout_ms)  # type: ignore
            return True
        except Exception:
            return False

    def _extract_tab_text(self, name: str, settle_ms: int = 250) -> str:
        """Click a tab by accessible name and return its panel text if available."""
        clicked = self._click_tab(name, timeout_ms=3000)
        if not clicked:
            return ""
        # allow DOM to render
        try:
            self.page.wait_for_timeout(settle_ms)
            # Prefer ARIA tabpanel matched by name
            panel = self.page.get_by_role("tabpanel", name=re.compile(name, re.I)).first  # type: ignore
            return panel.inner_text(timeout=3000).strip()
        except Exception:
            # Fallback to main region or body (last resort)
            try:
                return self.page.get_by_role("main").first.inner_text(timeout=2000).strip()  # type: ignore
            except Exception:
                try:
                    return self.page.locator("body").inner_text(timeout=2000).strip()
                except Exception:
                    return ""

    def _get_tabpanel(self, name: str):
        """Return a locator for a tabpanel by name with graceful fallbacks."""
        roles = SELECTORS["table_roles"]
        try:
            return self.page.get_by_role(roles["tabpanel"], name=re.compile(name, re.I)).first  # type: ignore
        except Exception:
            # Fallback to any tabpanel; some UIs don't label panels
            return self.page.locator(f'[role="{roles["tabpanel"]}"]').first  # type: ignore

    def _read_table_from_panel(self, panel_name: str) -> Dict[str, Any]:
        """Read a table inside a named tabpanel into headers + rows of dicts.

        Returns { headers: List[str], rows: List[Dict[str,str]] }. If no semantic roles
        are available, returns empty structures.
        """
        panel = self._get_tabpanel(panel_name)
        headers: list[str] = []
        rows: list[Dict[str, str]] = []
        roles = SELECTORS["table_roles"]
        try:
            header_nodes = panel.get_by_role(roles["columnheader"])  # type: ignore
            h_count = header_nodes.count()  # type: ignore
            for i in range(h_count):
                txt = header_nodes.nth(i).inner_text(timeout=2000).strip()  # type: ignore
                headers.append(txt)

            # Collect row nodes (skip header row if present)
            row_nodes = panel.get_by_role(roles["row"])  # type: ignore
            r_count = row_nodes.count()  # type: ignore
            for r in range(1 if h_count > 0 else 0, r_count):
                row = row_nodes.nth(r)  # type: ignore
                # cells can be role=cell or gridcell
                cells = row.get_by_role(roles["cell"])  # type: ignore
                if cells.count() == 0:  # type: ignore
                    cells = row.get_by_role(roles["gridcell"])  # type: ignore
                values: list[str] = []
                c_count = cells.count()  # type: ignore
                for c in range(c_count):
                    values.append(cells.nth(c).inner_text(timeout=1500).strip())  # type: ignore
                if values:
                    if headers and len(values) == len(headers):
                        rows.append({headers[i]: values[i] for i in range(len(headers))})
                    else:
                        rows.append({str(i): values[i] for i in range(len(values))})
        except Exception:
            pass
        return {"headers": headers, "rows": rows}

    def navigate_to_animal_profile(self, animal_id: str) -> None:
        """Navigate to a specific animal's profile page."""
        url = f"https://new.shelterluv.com/animal/{animal_id}"
        self.page.goto(url)

    def navigate_to_memos_page(self, internal_id: str) -> None:
        """Navigate to the memos page for an animal."""
        url = f"https://new.shelterluv.com/animals/{internal_id}/memos"
        self.page.goto(url)

    def navigate_to_person_profile(self, person_id: str) -> None:
        """Navigate to a specific person's profile page."""
        url = f"https://new.shelterluv.com/person/{person_id}"
        self.page.goto(url)

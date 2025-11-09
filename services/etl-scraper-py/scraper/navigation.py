"""
Navigation and UI interaction for ShelterLuv scraper.

Handles tab navigation, panel access, and table reading.
"""

from typing import Dict, Any, List
import re

# Navigation and table-related selectors
SELECTORS = {
    # Content anchors
    "case_manager_section": 'div:has-text("Case Manager")',
    # Generic memo content fallbacks (when no roles are available)
    "memo_selectors": [
        'div[class*="memo"]',
        '.memo-content',
        '[class*="memo"]',
        'pre',
        '.content'
    ],
    # Tab names used throughout scraping
    "tabs": {
        "behavioral": "Behavioral",
        "medical": "Medical",
        "history": "History",
        "files": "Files",
        "attributes": "Attributes",
        "memos": "Memos",
        "categories": "Categories",
        "profile": "Profile"
    },
    # Sub-tabs within main tabs
    "subtabs": {
        "behavioral": {
            "plan": "Plan",
            "assessment": "Assessment",
            "playgroups": "Playgroups",
            "behavior_checks": "Behavior Checks"
        },
        "medical": {
            "summary": "Summary",
            "diagnoses": "Diagnoses",
            "diagnostic_tests": "Diagnostic Tests",
            "vaccines": "Vaccines",
            "daily_observations": "Daily Observations",
            "physical_exams": "Physical Exams",
            "treatments": "Treatments",
            "procedures": "Procedures/Surgeries"
        },
        "history": {
            "intakes_outcomes": "Intakes/Outcomes",
            "caretakers": "Caretakers",
            "statuses": "Statuses",
            "locations": "Locations",
            "profile_edits": "Profile Edits"
        },
        "memos": {
            "latest": "Latest",
            "medical": "Medical"
        }
    },
    # CSS selectors for elements that might change
    "attributes_badges": '[class*="badge" i], [class*="chip" i]',
    # ARIA roles used for table parsing
    "table_roles": {
        "columnheader": "columnheader",
        "row": "row",
        "cell": "cell",
        "gridcell": "gridcell",
        "tabpanel": "tabpanel"
    }
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
            self.page.get_by_role("tab", name=name).first.click(timeout=timeout_ms)
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
            panel = self.page.get_by_role("tabpanel", name=re.compile(name, re.I)).first
            return panel.inner_text(timeout=3000).strip()
        except Exception:
            # Fallback to main region or body (last resort)
            try:
                return self.page.get_by_role("main").first.inner_text(timeout=2000).strip()
            except Exception:
                try:
                    return self.page.locator("body").inner_text(timeout=2000).strip()
                except Exception:
                    return ""

    def _get_tabpanel(self, name: str):
        """Return a locator for a tabpanel by name with graceful fallbacks."""
        roles = SELECTORS["table_roles"]
        try:
            return self.page.get_by_role(roles["tabpanel"], name=re.compile(name, re.I)).first
        except Exception:
            # Fallback to any tabpanel; some UIs don't label panels
            return self.page.locator(f'[role="{roles["tabpanel"]}"]').first

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
            header_nodes = panel.get_by_role(roles["columnheader"])
            h_count = header_nodes.count()
            for i in range(h_count):
                txt = header_nodes.nth(i).inner_text(timeout=2000).strip()
                headers.append(txt)

            # Collect row nodes (skip header row if present)
            row_nodes = panel.get_by_role(roles["row"])
            r_count = row_nodes.count()
            for r in range(1 if h_count > 0 else 0, r_count):
                row = row_nodes.nth(r)
                # cells can be role=cell or gridcell
                cells = row.get_by_role(roles["cell"])
                if cells.count() == 0:
                    cells = row.get_by_role(roles["gridcell"])
                values: list[str] = []
                c_count = cells.count()
                for c in range(c_count):
                    values.append(cells.nth(c).inner_text(timeout=1500).strip())
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
        url = f"https://new.shelterluv.com/animals/{animal_id}"
        self.page.goto(url)

    def navigate_to_memos_page(self, internal_id: str) -> None:
        """Navigate to the memos page for an animal."""
        url = f"https://new.shelterluv.com/animals/{internal_id}/memos"
        self.page.goto(url)

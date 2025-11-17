"""
Field-level parsing functions for history and administrative information.
Handles intake/outcome dates, case managers, status history, etc.
"""

from typing import Any, Dict, List

from .navigation import SELECTORS


def scrape_history_fields(navigation) -> Dict[str, List[Dict[str, Any]]]:
    """Scrape history subtabs."""
    result: Dict[str, List[Dict[str, Any]]] = {}
    history_tab = SELECTORS["tabs"]["history"]  # type: ignore
    if not navigation._click_tab(history_tab, timeout_ms=1500):
        return result

    subtabs = SELECTORS["subtabs"]["history"]  # type: ignore
    for subtab_key, key in [
        ("intakes_outcomes", "HistoryIntakesOutcomes"),
        ("caretakers", "HistoryCaretakers"),
        ("statuses", "HistoryStatuses"),
        ("locations", "HistoryLocations"),
        ("profile_edits", "HistoryProfileEdits"),
    ]:
        subtab_name = subtabs[subtab_key]
        if navigation._click_tab(subtab_name, timeout_ms=1200):
            table = navigation._read_table_from_panel(subtab_name)
            result[key] = table.get("rows", [])
    return result


def scrape_intake_outcome_fields(page, navigation) -> Dict[str, str]:
    """Scrape intake and outcome related fields."""
    result = {}

    # Intake information
    intake_fields = {
        "Intake Date": "IntakeDate",
        "Intake Type": "IntakeType",
        "Surrender Reason": "SurrenderReason",
        "Previous Owner": "PreviousOwner",
        "Transfer From": "TransferFrom",
    }

    # Outcome information
    outcome_fields = {
        "Outcome Date": "OutcomeDate",
        "Outcome Type": "OutcomeType",
        "Adopted By": "AdoptedBy",
        "Adoption Fee": "AdoptionFee",
        "Transferred To": "TransferredTo",
    }

    all_fields = {**intake_fields, **outcome_fields}

    for label_text, field_name in all_fields.items():
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


def extract_case_manager_from_categories(page, result: Dict[str, Any]) -> None:
    """Extract case manager information from the categories section."""
    try:
        # Look for case manager in categories section
        case_manager_selectors = [
            'text="Case Manager"',
            'text="Assigned Staff"',
            'text="Primary Contact"',
        ]

        for selector in case_manager_selectors:
            locator = page.locator(selector)
            if locator.count() > 0:
                container = locator.first.locator('xpath=ancestor::div[1]')
                if container.count() > 0:
                    full_text = container.first.inner_text(timeout=2000)
                    # Extract the value after the label
                    label_text = selector.replace('text="', '').replace('"', '')
                    if full_text.startswith(label_text):
                        value = full_text[len(label_text):].strip().lstrip(':').strip()
                        if value:
                            result["CaseManager"] = value
                            break
    except Exception:
        # Case manager is optional
        pass

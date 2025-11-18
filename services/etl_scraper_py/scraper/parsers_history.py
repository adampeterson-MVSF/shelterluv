"""
Field-level parsing functions for history and administrative information.
Handles intake/outcome dates, case managers, status history, etc.
"""

from typing import Any, Dict, List

from .navigation import SELECTORS
from .parsers_fields import extract_text_by_selector, extract_table_rows_as_dicts, normalize_date_string


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


def extract_event_history(page) -> List[Dict[str, Any]]:
    """Extract complete event history from the History section."""
    events = []

    try:
        # Look for the History section with event timeline
        history_section_selectors = [
            SELECTORS.get("history_section", ".history-section"),
            "[data-section='history']",
            ".history-events",
            "[id*='history']"
        ]

        for section_sel in history_section_selectors:
            try:
                # Look for event tables within the history section
                event_table_selectors = [
                    f"{section_sel} table",
                    f"{section_sel} .event-table",
                    "[data-testid*='event'] table"
                ]

                for table_sel in event_table_selectors:
                    try:
                        rows = extract_table_rows_as_dicts(
                            page,
                            table_sel,
                            [".event-type", ".date", ".person", ".details", ".status"]
                        )

                        if rows:
                            for row in rows:
                                event = {
                                    "event_type": row.get("Event Type", row.get("Type", "")),
                                    "date": normalize_date_string(row.get("Date", "")),
                                    "associated_person": row.get("Person", row.get("Associated Person", "")),
                                    "details": row.get("Details", ""),
                                    "status_change": row.get("Status", row.get("Status Change", ""))
                                }
                                if event["event_type"] or event["date"]:
                                    events.append(event)
                            break
                    except Exception:
                        continue

                if events:
                    break

            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting event history: {e}")

    return events


def extract_weight_history(page) -> List[Dict[str, Any]]:
    """Extract weight history from the medical records."""
    weight_history = []

    try:
        # Look for weight table in medical history section
        weight_table_selectors = [
            SELECTORS.get("weight_table", ".weight-history table"),
            ".weight-table",
            "[data-weight-history] table",
            ".medical-history .weight table"
        ]

        # Try a more direct approach: find the table that contains weight data
        try:
            # Look for any table that has a row containing weight-like data (kg or lbs)
            all_tables = page.locator("table")
            for table_idx in range(all_tables.count()):
                table = all_tables.nth(table_idx)
                rows_locator = table.locator("tbody tr")
                table_has_weight_data = False

                # Check first few rows for weight data
                for row_idx in range(min(3, rows_locator.count())):
                    row = rows_locator.nth(row_idx)
                    cells = row.locator("td")
                    if cells.count() >= 2:
                        first_cell = cells.nth(0).inner_text().strip()
                        # Check if first cell looks like weight (contains kg, lbs, or is a number)
                        if ('kg' in first_cell.lower() or 'lbs' in first_cell.lower() or
                            (first_cell.replace('.', '').replace(' ', '').isdigit() and len(first_cell) <= 5)):
                            table_has_weight_data = True
                            break

                if table_has_weight_data:
                    # Extract all rows from this table
                    for row_idx in range(rows_locator.count()):
                        row = rows_locator.nth(row_idx)
                        cells = row.locator("td")
                        if cells.count() >= 2:
                            weight_text = cells.nth(0).inner_text().strip()
                            date_text = cells.nth(1).inner_text().strip()
                            weight_entry = {
                                "weight": weight_text,
                                "date": normalize_date_string(date_text),
                                "unit": _extract_weight_unit(weight_text)
                            }
                            if weight_entry["weight"]:
                                weight_history.append(weight_entry)

                    return weight_history
        except Exception:
            pass

        # Fall back to the original approach
        try:
            weight_table_selector = ".space-y-2 .align-middle table"
            print(f"DEBUG: Trying weight table selector: {weight_table_selector}")
            rows = extract_table_rows_as_dicts(
                page,
                weight_table_selector,
                ["th:nth-child(1)", "th:nth-child(2)"]
            )
            print(f"DEBUG: Found {len(rows) if rows else 0} rows with specific selector")

            if rows:
                print(f"DEBUG: Processing {len(rows)} weight rows")
                for i, row in enumerate(rows):
                    print(f"DEBUG: Row {i}: {row}")
                    # Try different possible column names
                    weight_value = row.get("Weight", "") or row.get("col_0", "")
                    date_value = row.get("Date", "") or row.get("col_1", "")
                    weight_entry = {
                        "weight": weight_value,
                        "date": normalize_date_string(date_value),
                        "unit": _extract_weight_unit(weight_value)
                    }
                    print(f"DEBUG: Weight entry: {weight_entry}")
                    if weight_entry["weight"]:
                        weight_history.append(weight_entry)

                print(f"DEBUG: Final weight_history: {weight_history}")
                return weight_history
        except Exception as e:
            print(f"DEBUG: Specific selector failed: {e}")

        # Fall back to the original approach
        for table_sel in weight_table_selectors:
            try:
                rows = extract_table_rows_as_dicts(
                    page,
                    table_sel,
                    ["th:nth-child(1)", "th:nth-child(2)", "th:nth-child(3)"]
                )

                if rows:
                    for row in rows:
                        weight_entry = {
                            "weight": row.get("Weight", ""),
                            "date": normalize_date_string(row.get("Date", "")),
                            "unit": _extract_weight_unit(row.get("Weight", ""))
                        }
                        if weight_entry["weight"]:
                            weight_history.append(weight_entry)
                    break

            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting weight history: {e}")

    return weight_history


def extract_category_history(page) -> List[Dict[str, Any]]:
    """Extract category assignment history."""
    category_history = []

    try:
        # Look for categories table in history section
        categories_table_selectors = [
            SELECTORS.get("categories_table", ".categories-history table"),
            ".categories-table",
            "[data-categories] table",
            ".history .categories table"
        ]

        for table_sel in categories_table_selectors:
            try:
                rows = extract_table_rows_as_dicts(
                    page,
                    table_sel,
                    [".category", ".date", ".assigned-by", ".details"]
                )

                if rows:
                    for row in rows:
                        category_entry = {
                            "category": row.get("Category", ""),
                            "date": normalize_date_string(row.get("Date", "")),
                            "assigned_by": row.get("Assigned By", row.get("Person", "")),
                            "details": row.get("Details", "")
                        }
                        if category_entry["category"]:
                            category_history.append(category_entry)
                    break

            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting category history: {e}")

    return category_history


def extract_compatibility_warnings(page) -> List[Dict[str, Any]]:
    """Extract structured compatibility warnings from disclaimers section."""
    warnings = []

    try:
        # Look for disclaimer sections with warnings
        disclaimer_selectors = [
            ".disclaimers .border-l-8",
            "[data-section='disclaimers'] .warning",
            ".disclaimers div[class*='border-l']"
        ]

        for disclaimer_sel in disclaimer_selectors:
            try:
                warning_elements = page.locator(disclaimer_sel).all()
                for element in warning_elements:
                    try:
                        # Extract warning title and content
                        title_element = element.locator("h3").first
                        content_element = element.locator(".text-sm").first

                        if title_element.count() > 0 and content_element.count() > 0:
                            title = title_element.inner_text(timeout=1000).strip()
                            content = content_element.inner_text(timeout=1000).strip()

                            # Parse warning type and severity from title
                            warning_type, severity = _parse_warning_title(title)

                            warning = {
                                "warning_type": warning_type,
                                "severity": severity,
                                "details": content,
                                "date_noted": None  # Could be extracted from content if available
                            }
                            warnings.append(warning)

                    except Exception:
                        continue

            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting compatibility warnings: {e}")

    return warnings


def extract_attached_documents(page) -> List[Dict[str, Any]]:
    """Extract list of attached documents and files."""
    documents = []

    try:
        # Look for files section
        files_section_selectors = [
            ".files-section",
            "[data-section='files']",
            "#files",
            ".attached-files"
        ]

        for section_sel in files_section_selectors:
            try:
                # Look for file links or entries
                file_selectors = [
                    f"{section_sel} a[href*='shelterluv']",
                    f"{section_sel} .file-entry",
                    f"{section_sel} .document-link"
                ]

                for file_sel in file_selectors:
                    try:
                        file_elements = page.locator(file_sel).all()
                        for element in file_elements:
                            try:
                                # Extract file information
                                filename = element.inner_text(timeout=1000).strip()
                                href = element.get_attribute("href", timeout=1000)

                                if filename and href:
                                    # Determine file type from filename or URL
                                    file_type = _determine_file_type(filename, href)

                                    document = {
                                        "filename": filename,
                                        "file_type": file_type,
                                        "upload_date": None,  # Would need additional parsing
                                        "description": "",  # Would need additional parsing
                                        "url": href
                                    }
                                    documents.append(document)

                            except Exception:
                                continue

                        if documents:
                            break

                    except Exception:
                        continue

                if documents:
                    break

            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting attached documents: {e}")

    return documents


def _extract_weight_unit(weight_str: str) -> str:
    """Extract weight unit from weight string."""
    if not weight_str:
        return "lbs"  # Default

    weight_lower = weight_str.lower()
    if "kg" in weight_lower:
        return "kg"
    elif "lbs" in weight_lower or "lb" in weight_lower:
        return "lbs"
    else:
        return "lbs"  # Default assumption


def _parse_warning_title(title: str) -> tuple[str, str]:
    """Parse warning type and severity from disclaimer title."""
    title_lower = title.lower()

    # Extract warning type
    if "cat compatibility" in title_lower:
        warning_type = "Cat Compatibility"
    elif "kid compatibility" in title_lower or "children" in title_lower:
        warning_type = "Kid Compatibility"
    elif "dog compatibility" in title_lower:
        warning_type = "Dog Compatibility"
    elif "energy level" in title_lower:
        warning_type = "Energy Level"
    elif "dental" in title_lower:
        warning_type = "Dental Disease"
    elif "heart murmur" in title_lower:
        warning_type = "Heart Murmur"
    elif "stair" in title_lower:
        warning_type = "Stairs"
    elif "potty training" in title_lower:
        warning_type = "Potty Training"
    elif "events" in title_lower:
        warning_type = "Events"
    else:
        warning_type = title.split(" - ")[0].strip() if " - " in title else title

    # Extract severity
    if "unknown" in title_lower:
        severity = "Unknown"
    elif "not recommended" in title_lower or "caution" in title_lower:
        severity = "Caution"
    else:
        severity = "Unknown"

    return warning_type, severity


def _determine_file_type(filename: str, url: str) -> str:
    """Determine file type from filename and URL."""
    filename_lower = filename.lower()
    url_lower = url.lower()

    if any(ext in filename_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
        return "photo"
    elif any(ext in filename_lower for ext in ['.pdf']):
        return "document"
    elif any(ext in filename_lower for ext in ['.doc', '.docx']):
        return "document"
    elif 'photo' in filename_lower or 'image' in filename_lower:
        return "photo"
    elif 'document' in filename_lower or 'record' in filename_lower:
        return "document"
    else:
        return "file"

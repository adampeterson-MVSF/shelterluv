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
        # Find the h1 with "History" text, then look for tables in the following content
        history_header = page.locator("h1:has-text('History')")
        if history_header.count() == 0:
            return events

        # Get the parent section containing the history header
        history_section = history_header.locator("xpath=ancestor::div[contains(@class, 'space-y-4')]").first
        if history_section.count() == 0:
            return events

        # Look for event tables within the history section
        event_table_selectors = [
            "table",
            ".event-table",
            "[data-testid*='event'] table"
        ]

        # Try to find the table directly after the History header
        try:
            # Use XPath to find table after History h1
            table_xpath = "//h1[normalize-space()='History']/following::table[1]"
            table_locator = page.locator(f"xpath={table_xpath}")

            if table_locator.count() > 0:
                # Extract table data manually since extract_table_rows_as_dicts expects a selector
                rows_locator = table_locator.locator("tbody tr")
                rows = []

                for i in range(rows_locator.count()):
                    row = rows_locator.nth(i)
                    cells = row.locator("td")
                    if cells.count() >= 5:  # Date, Visit#, Event, Person/Partner, Jurisdiction, User
                        row_data = {
                            "Date": cells.nth(0).inner_text().strip(),
                            "Visit #": cells.nth(1).inner_text().strip(),
                            "Event": cells.nth(2).inner_text().strip(),
                            "Person/Partner": cells.nth(3).inner_text().strip(),
                            "Jurisdiction": cells.nth(4).inner_text().strip(),
                            "User": cells.nth(5).inner_text().strip() if cells.count() > 5 else ""
                        }
                        rows.append(row_data)

                if rows:
                    for row in rows:
                        event = {
                            "event_type": row.get("Event", ""),
                            "date": normalize_date_string(row.get("Date", "")),
                            "associated_person": row.get("Person/Partner", ""),
                            "details": "",
                            "status_change": ""
                        }
                        if event["event_type"] or event["date"]:
                            events.append(event)
        except Exception:
            pass

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

        # Fall back to CSS selector approach
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
        # Find the Categories header and then the table
        try:
            categories_header = page.locator("h4:has-text('Categories')")
            if categories_header.count() > 0:
                # Look for table in the general vicinity after the categories header
                table_locator = page.locator("h4:has-text('Categories') ~ div table").first
                if table_locator.count() > 0:
                        # Extract table data manually
                        rows_locator = table_locator.locator("tbody tr")
                        rows = []

                        for i in range(rows_locator.count()):
                            row = rows_locator.nth(i)
                            cells = row.locator("td")
                            if cells.count() >= 5:  # Date, Category Type, Previous Value, New Value, User
                                row_data = {
                                    "Date": cells.nth(0).inner_text().strip(),
                                    "Category Type": cells.nth(1).inner_text().strip(),
                                    "Previous Value": cells.nth(2).inner_text().strip(),
                                    "New Value": cells.nth(3).inner_text().strip(),
                                    "User": cells.nth(4).inner_text().strip()
                                }
                                rows.append(row_data)

                        if rows:
                            for row in rows:
                                category_entry = {
                                    "category": row.get("Category Type", ""),
                                    "date": normalize_date_string(row.get("Date", "")),
                                    "old_value": row.get("Previous Value", ""),
                                    "new_value": row.get("New Value", ""),
                                    "assigned_by": row.get("User", ""),
                                    "details": ""
                                }
                                if category_entry["category"]:
                                    category_history.append(category_entry)
        except Exception:
            pass

    except Exception as e:
        print(f"Error extracting category history: {e}")

    return category_history


def extract_compatibility_warnings(page) -> List[Dict[str, Any]]:
    """Extract structured compatibility warnings from disclaimers section."""
    warnings = []

    try:
        # Look for disclaimer sections with warnings
        # Find disclaimers section and extract warning blocks
        try:
            disclaimer_header = page.locator("h1:has-text('Disclaimers')")
            if disclaimer_header.count() > 0:
                # Look for warning elements after the disclaimers header
                warning_elements = page.locator("h1:has-text('Disclaimers') ~ div .border-l-8").all()
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
            pass

    except Exception as e:
        print(f"Error extracting compatibility warnings: {e}")

    return warnings


def extract_attached_documents(page) -> List[Dict[str, Any]]:
    """Extract list of attached documents and files."""
    documents = []

    try:
        # Look for files section
        try:
            files_header = page.locator("h1:has-text('Files')")
            if files_header.count() > 0:
                # Look for file links after the files header
                file_selectors = [
                    "h1:has-text('Files') ~ div a[href*='signed/document']",
                    "h1:has-text('Files') ~ div .flex.justify-between.items-center.text-sm.border-b a",
                    "h1:has-text('Files') ~ div .flex.justify-between.items-center a"
                ]

                for file_sel in file_selectors:
                    try:
                        file_elements = page.locator(file_sel).all()
                        for element in file_elements:
                            try:
                                # Handle different element types
                                if "signed/document" in file_sel:
                                    # Direct anchor tag
                                    filename = element.inner_text(timeout=1000).strip()
                                    href = element.get_attribute("href", timeout=1000)
                                    date_element = element.locator("xpath=following-sibling::div[@class='text-black']").first
                                    upload_date = None
                                    if date_element.count() > 0:
                                        upload_date = date_element.inner_text(timeout=1000).strip()
                                else:
                                    # Container div - find anchor inside
                                    anchor = element.locator("a").first
                                    if anchor.count() > 0:
                                        filename = anchor.inner_text(timeout=1000).strip()
                                        href = anchor.get_attribute("href", timeout=1000)
                                        date_element = element.locator(".text-black").first
                                        upload_date = None
                                        if date_element.count() > 0:
                                            upload_date = date_element.inner_text(timeout=1000).strip()
                                    else:
                                        continue

                                if filename and href:
                                    # Determine file type from filename or URL
                                    file_type = _determine_file_type(filename, href)

                                    document = {
                                        "filename": filename,
                                        "file_type": file_type,
                                        "upload_date": upload_date,
                                        "description": "",  # Could be enhanced later
                                        "url": href
                                    }
                                    documents.append(document)

                                if documents:
                                    break

                            except Exception:
                                continue

                    except Exception:
                        continue

        except Exception:
            pass

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


def extract_disclaimers(page) -> list:
    """Extract disclaimers section from ShelterLuv summary page."""
    disclaimers = []

    try:
        # Find the disclaimers section
        disclaimer_header = page.locator("h1:has-text('Disclaimers')")
        if disclaimer_header.count() == 0:
            return disclaimers

        # Find all disclaimer items - they are descendants of sibling divs with border-l-8 border-green-600
        disclaimer_items = page.locator("h1:has-text('Disclaimers') ~ div .border-l-8.border-green-600")

        for i in range(disclaimer_items.count()):
            try:
                item = disclaimer_items.nth(i)
                title_elem = item.locator("h3.text-sm.leading-tight.font-semibold")
                content_elem = item.locator("div.text-sm.text-black")

                title = title_elem.inner_text(timeout=1000).strip() if title_elem.count() > 0 else ""
                content = content_elem.inner_text(timeout=1000).strip() if content_elem.count() > 0 else ""

                if title:
                    # Categorize the disclaimer based on content
                    category = _categorize_disclaimer(title, content)

                    disclaimers.append({
                        "title": title,
                        "content": content,
                        "category": category
                    })

            except Exception as e:
                print(f"Error extracting disclaimer {i}: {e}")
                continue

    except Exception as e:
        print(f"Error extracting disclaimers: {e}")

    return disclaimers


def _categorize_disclaimer(title: str, content: str) -> str:
    """Categorize a disclaimer based on its title and content."""
    title_lower = title.lower()
    content_lower = content.lower()

    if any(word in title_lower for word in ['cat', 'dog', 'kid', 'child', 'family']):
        return "compatibility"
    elif any(word in title_lower for word in ['energy', 'exercise', 'activity', 'stair', 'house']):
        return "housing"
    elif any(word in title_lower for word in ['dental', 'heart', 'medical', 'disease']):
        return "medical"
    elif any(word in title_lower for word in ['potty', 'train', 'behavior', 'bark', 'lung', 'leash']):
        return "behavior"
    elif any(word in content_lower for word in ['intake', 'return', 'adoption']):
        return "behavior"
    else:
        return "other"


def extract_website_memo(page) -> dict:
    """Extract website memo/kennel card content."""
    website_memo = {}

    try:
        # Find the website memo section
        memo_header = page.locator("h3:has-text('Kennel Card / Website Memo')")
        if memo_header.count() == 0:
            return website_memo

        # Get the parent container
        memo_container = memo_header.locator("xpath=ancestor::div[contains(@class, 'border-l-8')]").first
        if memo_container.count() == 0:
            return website_memo

        # Extract author and date
        author_date_elem = memo_container.locator("div.text-xs.text-gray-600")
        author = ""
        date = ""

        if author_date_elem.count() > 0:
            author_date_text = author_date_elem.inner_text(timeout=1000).strip()
            # Parse "MM/DD/YYYY by Author Name"
            if " by " in author_date_text:
                date_part, author_part = author_date_text.split(" by ", 1)
                date = date_part.strip()
                author = author_part.strip()

        # Extract content
        content_elem = memo_container.locator("div.text-sm.text-black")
        content = content_elem.inner_text(timeout=1000).strip() if content_elem.count() > 0 else ""

        if author or date or content:
            website_memo = {
                "author": author,
                "date": date,
                "content": content
            }

    except Exception as e:
        print(f"Error extracting website memo: {e}")

    return website_memo

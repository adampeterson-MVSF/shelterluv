"""
Field-level parsing functions for ShelterLuv scraper.
One function per field or field group. Pure extraction logic.
"""

from typing import Dict, Any, List
from .navigation import SELECTORS

# Mapping from scraped category names to schema field names
CATEGORY_MAP = {
    "Adoption Category": "AdoptionCategory",
    "Medical Category": "MedicalCategory",
    "Behavior Category": "BehaviorCategory",
    "Volunteer Category": "VolunteerCategory",
}


def parse_categories_from_text(text: str) -> Dict[str, str]:
    """
    Parse category information from ShelterLuv profile text.
    Returns dict with AdoptionCategory, MedicalCategory, BehaviorCategory, VolunteerCategory keys.
    Handles formats like:
    - "Category Name: Value" (same line)
    - "Category Name" (category on one line, value on next line)
    - HTML content with structured category sections
    - wire:snapshot JSON data (preferred method)
    """
    categories = {}
    lines = text.split('\n')

    # First, try to parse wire:snapshot JSON data (most reliable)
    if 'wire:snapshot' in text:
        try:
            import json
            import html
            import re

            # Extract JSON from wire:snapshot attribute (handle HTML escaping)
            snapshot_match = re.search(r'wire:snapshot\s*=\s*["\']({.*?})["\']', text, re.DOTALL)
            if snapshot_match:
                json_str = snapshot_match.group(1)
                json_str = html.unescape(json_str)  # Unescape HTML entities
                data = json.loads(json_str)

                # Extract category IDs from animal data
                animal_data = data.get('data', {}).get('animal', [{}])[0]
                behavior_id = animal_data.get('behavior_category_id')
                volunteer_id = animal_data.get('volunteer_category_id')
                medical_id = animal_data.get('medical_category_id')
                adoption_id = animal_data.get('adoption_category_id')

                # Helper function to find category name by ID
                def find_category_name(categories_list, category_id):
                    if not category_id:
                        return 'None'
                    # Handle nested array structure
                    if isinstance(categories_list, list) and len(categories_list) > 0:
                        categories_list = categories_list[0] if isinstance(categories_list[0], list) else categories_list
                        for category in categories_list:
                            if isinstance(category, dict) and category.get('id') == category_id:
                                return category.get('name', 'Unknown')
                    return 'Unknown'

                # Extract category lists and resolve names
                category_data = data.get('data', {})
                if behavior_id is not None:
                    categories['BehaviorCategory'] = find_category_name(category_data.get('behaviorCategories', []), behavior_id)
                if volunteer_id is not None:
                    categories['VolunteerCategory'] = find_category_name(category_data.get('volunteerCategories', []), volunteer_id)
                if medical_id is not None:
                    categories['MedicalCategory'] = find_category_name(category_data.get('medicalCategories', []), medical_id)
                if adoption_id is not None:
                    categories['AdoptionCategory'] = find_category_name(category_data.get('adoptionCategories', []), adoption_id)

                return categories  # Return early if we successfully parsed wire:snapshot
        except Exception as e:
            # If JSON parsing fails, continue with other methods
            pass

    # Fallback: try to parse "Category Name: Value" format on the same line
    for line in lines:
        line = line.strip()
        for category_key, schema_key in CATEGORY_MAP.items():
            if line.startswith(category_key + ':'):
                value = line[len(category_key + ':'):].strip()
                categories[schema_key] = value
                break

    # If we didn't find categories with the colon format, try the old format
    # (category on one line, value on next line)
    if not categories:
        for i, line in enumerate(lines):
            line = line.strip()
            if line in CATEGORY_MAP:
                if i + 1 < len(lines):
                    categories[CATEGORY_MAP[line]] = lines[i + 1].strip()

    # Try to parse HTML content with specific selectors for ShelterLuv categories
    if not categories and ('Categories' in text or 'Behavior Category' in text):
        import re

        # Simple approach: find all inline-editable buttons and associate with preceding labels
        # Look for patterns like: Category Name</label> ... inline-editable">VALUE</button>

        # Find all button values (handle both escaped and unescaped quotes)
        button_matches = re.findall(r'inline-editable[^>]*>\s*([^<\n]+?)\s*</button', text, re.IGNORECASE)

        # Find all category labels
        label_matches = re.findall(r'<label[^>]*>\s*([^<\n]*?Category)\s*</label>', text, re.IGNORECASE)

        # Associate labels with button values (assuming they appear in order)
        for i, (label, value) in enumerate(zip(label_matches, button_matches)):
            value = value.strip()
            if value and value.lower() != 'none':
                if 'Adoption Category' in label:
                    categories['AdoptionCategory'] = value
                elif 'Medical Category' in label:
                    categories['MedicalCategory'] = value
                elif 'Behavior Category' in label:
                    categories['BehaviorCategory'] = value
                elif 'Volunteer Category' in label:
                    categories['VolunteerCategory'] = value

    return categories


def parse_case_manager_from_adoption_category(adoption_category_text: str) -> str | None:
    """
    Extract case manager name from Adoption Category text.
    
    Strategies:
    - Look for patterns like "Case Manager: Jane Doe"
    - If Adoption Category is formatted as "Jane Doe – Something", take the name part
    - Handle "None assigned" or empty patterns
    
    Returns case manager name or None if not found.
    """
    if not adoption_category_text or not isinstance(adoption_category_text, str):
        return None
    
    text = adoption_category_text.strip()
    if not text or text.lower() in ['none', 'none assigned', 'not assigned', 'unassigned', '']:
        return None
    
    # Strategy 1: Look for explicit "Case Manager:" pattern
    import re
    case_manager_match = re.search(r'case\s+manager\s*:?\s*([^–\n]+)', text, re.IGNORECASE)
    if case_manager_match:
        name = case_manager_match.group(1).strip()
        if name and name.lower() not in ['none', 'none assigned', 'not assigned']:
            return name
    
    # Strategy 2: If Adoption Category is formatted as "Name – Category", extract name
    # Common pattern: "Jane Doe – Available" or "John Smith – Pending"
    dash_match = re.match(r'^([^–]+?)\s*–\s*.+', text)
    if dash_match:
        name = dash_match.group(1).strip()
        # Validate it looks like a name (has at least one space or is reasonable length)
        if name and len(name) > 2 and name.lower() not in ['none', 'not assigned']:
            return name
    
    # Strategy 3: If the whole text is just a name (no special formatting), use it
    # But only if it's reasonable (2-50 chars, not all caps acronyms)
    if len(text) >= 2 and len(text) <= 50 and not re.match(r'^[A-Z\s]{3,}$', text):
        # Check if it contains typical name patterns
        if re.search(r'[a-z]', text):  # Has lowercase (not all caps acronym)
            return text
    
    return None


def scrape_categories_from_table(navigation, table: Dict[str, Any]) -> Dict[str, str]:
    """Scrape categories from structured table format."""
    categories: Dict[str, str] = {}
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
    if "Volunteer Category" in latest_by_category:
        categories["VolunteerCategory"] = latest_by_category["Volunteer Category"]

    return categories


def scrape_behavioral_fields(page, navigation) -> Dict[str, str]:
    """Scrape behavioral tab data."""
    result: Dict[str, str] = {}
    behavioral_tab = SELECTORS["tabs"]["behavioral"]  # type: ignore
    if not navigation._click_tab(behavioral_tab, timeout_ms=2000):
        return result

    subtabs = SELECTORS["subtabs"]["behavioral"]  # type: ignore
    result["BehaviorPlan"] = navigation._extract_tab_text(subtabs["plan"])  # type: ignore
    result["BehaviorAssessment"] = navigation._extract_tab_text(subtabs["assessment"])  # type: ignore
    result["BehaviorPlaygroups"] = navigation._extract_tab_text(subtabs["playgroups"])  # type: ignore
    result["BehaviorChecks"] = navigation._extract_tab_text(subtabs["behavior_checks"])  # type: ignore
    return result


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


def scrape_attributes(page, navigation) -> Dict[str, List[str]]:
    """Scrape attributes (badges/chips) from the main profile content."""
    # Look for elements with wire:key starting with "behave-attr" or "phys-attr"
    try:
        # Wait a bit for dynamic content to load
        page.wait_for_timeout(2000)

        # Get both behavioral and physical attributes
        behave_elements = page.locator('[wire\\:key^="behave-attr-"]')
        phys_elements = page.locator('[wire\\:key^="phys-attr-"]')

        all_elements = []
        # Add behavioral attributes
        for i in range(behave_elements.count()):
            all_elements.append(behave_elements.nth(i))
        # Add physical attributes
        for i in range(phys_elements.count()):
            all_elements.append(phys_elements.nth(i))

        # If no wire:key elements found, try fallback immediately
        if not all_elements:
            fallback_result = _scrape_attributes_fallback(page, navigation)
            # Categorize the fallback results
            behavioral_keywords = [
                'compatibility', 'energy level', 'events', 'stairs', 'bio', 'intake notes',
                'kid', 'cat', 'dog', 'has bio', 'has intake'
            ]
            behavioral = []
            physical = []
            for attr in fallback_result:
                attr_lower = attr.lower()
                if any(keyword in attr_lower for keyword in behavioral_keywords):
                    behavioral.append(attr)
                else:
                    physical.append(attr)
            return {
                'behavioral': list(set(behavioral)),
                'physical': list(set(physical))
            }

        if all_elements:
            values = []
            for elem in all_elements:
                try:
                    # Get the text from the p tag inside the badge
                    p_tag = elem.locator('p')
                    if p_tag.count() > 0:
                        txt = p_tag.inner_text(timeout=500).strip()
                        if txt and len(txt) > 3:  # Attributes should be meaningful text
                            values.append(txt)
                except:
                    continue

            if values:
                # Clean up the attributes (remove numbering and duplicates)
                cleaned_values = []
                for val in values:
                    # Remove the "1. " prefix if present
                    if val.startswith('1. '):
                        val = val[3:]
                    # Remove the "2. " prefix if present (for medical attributes)
                    if val.startswith('2. '):
                        val = val[3:]
                    cleaned_values.append(val.strip())

                # Remove duplicates and return
                unique_values = list(set(cleaned_values))
                return unique_values
    except Exception as e:
        print(f"Error scraping attributes with wire:key: {e}")

    # Fallback: look for the Attributes section and extract from there
    try:
        # Find the attributes section by looking for the header "Attributes"
        attributes_header = page.locator('p:has-text("Attributes")')
        if attributes_header.count() > 0:
            # Get the parent div that contains the attributes section
            attributes_section = attributes_header.locator('xpath=ancestor::div[contains(@class, "rounded-lg")]')
            if attributes_section.count() > 0:
                # Look for badge-like elements within this section
                badge_elements = attributes_section.locator('div[class*="inline-flex"]').all()
                values = []
                for elem in badge_elements:
                    try:
                        p_tag = elem.locator('p')
                        if p_tag.count() > 0:
                            txt = p_tag.inner_text(timeout=500).strip()
                            if txt and len(txt) > 3 and not txt.startswith('This will'):
                                values.append(txt)
                    except:
                        continue

                # Remove duplicates and return
                unique_values = list(set(values))
                if unique_values:
                    return unique_values
    except Exception as e:
        print(f"Error scraping attributes from section: {e}")

    # Always return the expected dictionary format
    return {'behavioral': [], 'physical': []}


def _scrape_attributes_fallback(page, navigation) -> List[str]:
    """Fallback method to scrape all attributes as a flat list."""
    # Try multiple approaches to find attributes
    try:
        # First, look for any elements with badge/chip classes anywhere on the page
        badge_selectors = [
            '[class*="badge"]',
            '[class*="chip"]',
            'span[class*="inline-flex"]',
            'div[class*="inline-flex"]'
        ]

        for selector in badge_selectors:
            badges = page.locator(selector)
            count = badges.count()
            if count > 0 and count < 50:  # Reasonable number
                values = []
                for i in range(count):
                    try:
                        txt = badges.nth(i).inner_text(timeout=1000).strip()
                        if txt and len(txt) > 2 and len(txt) < 100:
                            # Clean up numbering and filter
                            if txt.startswith('1. ') or txt.startswith('2. '):
                                txt = txt[3:]
                            if not txt.startswith('This will') and not 'will be included' in txt:
                                values.append(txt.strip())
                    except:
                        continue

                if values:
                    # If fallback returns a list, categorize it
                    behavioral_keywords = [
                        'compatibility', 'energy level', 'events', 'stairs', 'bio', 'intake notes',
                        'kid', 'cat', 'dog', 'has bio', 'has intake'
                    ]
                    behavioral = []
                    physical = []
                    for attr in list(set(values)):
                        attr_lower = attr.lower()
                        if any(keyword in attr_lower for keyword in behavioral_keywords):
                            behavioral.append(attr)
                        else:
                            physical.append(attr)
                    return {
                        'behavioral': behavioral,
                        'physical': physical
                    }

    except Exception as e:
        print(f"Error in fallback scraping: {e}")

    return {'behavioral': [], 'physical': []}


def scrape_files_table(navigation) -> List[Dict[str, str]]:
    """Scrape files table."""
    files_tab = SELECTORS["tabs"]["files"]  # type: ignore
    if not navigation._click_tab(files_tab, timeout_ms=1500):
        return []

    table = navigation._read_table_from_panel(files_tab)
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
    return normalized


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


def scrape_memos_from_profile(page, navigation) -> Dict[str, List[str]]:
    """Scrape memos from profile Memos tab."""
    result: Dict[str, List[str]] = {}
    memos_tab = SELECTORS["tabs"]["memos"]  # type: ignore
    if not navigation._click_tab(memos_tab, timeout_ms=1500):
        return result

    subtabs = SELECTORS["subtabs"]["memos"]  # type: ignore
    for subtab_key, key in [("latest", "MemosLatest"), ("medical", "MemosMedical")]:
        subtab_name = subtabs[subtab_key]
        if navigation._click_tab(subtab_name, timeout_ms=1000):
            try:
                panel = navigation._get_tabpanel(subtab_name)
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
    return result


def scrape_profile_main_content(page) -> str:
    """Scrape the main profile content, including categories section."""
    # First try to get the case manager section
    main_content = page.locator(SELECTORS["case_manager_section"])
    if main_content.count() > 0:
        case_manager_text = main_content.first.inner_text(timeout=5000)  # type: ignore
    else:
        case_manager_text = ""

    # Also try to get the categories section which might be separate
    # Look for the div containing the Categories header
    categories_content = page.locator('div:has-text("Categories")')
    if categories_content.count() > 0:
        # Only get the inner text, not the full HTML to avoid size issues
        categories_text = categories_content.first.inner_text(timeout=3000)  # type: ignore
    else:
        categories_text = ""

    # Combine both sections
    full_text = f"{case_manager_text}\n\n{categories_text}".strip()
    return full_text


def scrape_memos_page(page, internal_id: str) -> str:
    """
    Scrape the memos/documents page for raw HTML content.
    Returns memo text or empty string.
    """
    url_memos = f"https://new.shelterluv.com/animals/documents/memos?animals={internal_id}"
    page.goto(url_memos, timeout=10000)

    for selector in SELECTORS["memo_selectors"]:
        memo_elements = page.locator(selector)
        if memo_elements.count() > 0:
            all_memos = []
            for i in range(memo_elements.count()):
                memo_text = memo_elements.nth(i).inner_text(timeout=2000).strip()
                if memo_text:
                    all_memos.append(memo_text)

            if all_memos:
                return "\n\n".join(all_memos)

    # Fallback: try to get body text if no structured memos found
    page_text = page.locator('body').inner_text(timeout=3000)
    if any(keyword in page_text for keyword in ["Medical", "Intake", "Behavior"]):
        return page_text.strip()

    return ""


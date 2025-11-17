"""
Category-level parsing functions for ShelterLuv scraper.
Handles Adoption, Medical, Behavior, and Volunteer categories.
Prefers structured JSON data, falls back to HTML parsing.
"""

from typing import Any, Dict, List

from .navigation import SELECTORS


# Mapping from scraped category names to schema field names
CATEGORY_MAP = {
    "Adoption Category": "AdoptionCategory",
    "Medical Category": "MedicalCategory",
    "Behavior Category": "BehaviorCategory",
    "Volunteer Category": "VolunteerCategory",
}


def parse_categories_from_raw_record(raw_record: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract categories from a canonical raw animal record.
    Prefers structured JSON data from wire:snapshot, falls back to HTML text parsing.

    Args:
        raw_record: Canonical raw animal record with keys like 'html_content', 'json_data', etc.

    Returns:
        Dict with AdoptionCategory, MedicalCategory, BehaviorCategory, VolunteerCategory keys.
    """
    # First try wire:snapshot JSON data (most reliable)
    json_data = raw_record.get('json_data', {})
    if json_data:
        categories = _parse_categories_from_json(json_data)
        if categories:
            return categories

    # Fallback to HTML text parsing
    html_content = raw_record.get('html_content', '')
    if html_content:
        return parse_categories_from_text(html_content)

    return {}


def _parse_categories_from_json(json_data: Dict[str, Any]) -> Dict[str, str]:
    """Extract category IDs from wire:snapshot JSON and resolve to names."""
    categories = {}

    try:
        # Extract category IDs from animal data
        animal_data = json_data.get("data", {}).get("animal", [{}])[0]
        behavior_id = animal_data.get("behavior_category_id")
        volunteer_id = animal_data.get("volunteer_category_id")
        medical_id = animal_data.get("medical_category_id")
        adoption_id = animal_data.get("adoption_category_id")

        # Helper function to find category name by ID
        def find_category_name(categories_list, category_id):
            if not category_id:
                return "None"
            # Handle nested array structure
            if isinstance(categories_list, list) and len(categories_list) > 0:
                categories_list = (
                    categories_list[0]
                    if isinstance(categories_list[0], list)
                    else categories_list
                )
                for category in categories_list:
                    if isinstance(category, dict) and category.get("id") == category_id:
                        return category.get("name", "Unknown")
            return "Unknown"

        # Extract category lists and resolve names
        category_data = json_data.get("data", {})
        if behavior_id is not None:
            categories["BehaviorCategory"] = find_category_name(
                category_data.get("behaviorCategories", []), behavior_id
            )
        if volunteer_id is not None:
            categories["VolunteerCategory"] = find_category_name(
                category_data.get("volunteerCategories", []), volunteer_id
            )
        if medical_id is not None:
            categories["MedicalCategory"] = find_category_name(
                category_data.get("medicalCategories", []), medical_id
            )
        if adoption_id is not None:
            categories["AdoptionCategory"] = find_category_name(
                category_data.get("adoptionCategories", []), adoption_id
            )

        return categories
    except Exception:
        return {}


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
    lines = text.split("\n")

    # First, try to parse wire:snapshot JSON data (most reliable)
    if "wire:snapshot" in text:
        try:
            import html
            import json
            import re

            # Extract JSON from wire:snapshot attribute (handle HTML escaping)
            snapshot_match = re.search(r'wire:snapshot\s*=\s*["\']({.*?})["\']', text, re.DOTALL)
            if snapshot_match:
                json_str = snapshot_match.group(1)
                json_str = html.unescape(json_str)  # Unescape HTML entities
                data = json.loads(json_str)
                return _parse_categories_from_json(data)
        except Exception:
            # If JSON parsing fails, continue with other methods
            pass

    # Fallback: try to parse "Category Name: Value" format on the same line
    for line in lines:
        line = line.strip()
        for category_key, schema_key in CATEGORY_MAP.items():
            if line.startswith(category_key + ":"):
                value = line[len(category_key + ":") :].strip()
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
    if not categories and ("Categories" in text or "Behavior Category" in text):
        import re

        # Simple approach: find all inline-editable buttons and associate with preceding labels
        # Look for patterns like: Category Name</label> ... inline-editable">VALUE</button>
        # Find all button values (handle both escaped and unescaped quotes)
        button_matches = re.findall(
            r"inline-editable[^>]*>\s*([^<\n]+?)\s*</button", text, re.IGNORECASE
        )

        # Find all category labels
        label_matches = re.findall(
            r"<label[^>]*>\s*([^<\n]*?Category)\s*</label>", text, re.IGNORECASE
        )

        # Associate labels with button values (assuming they appear in order)
        for i, (label, value) in enumerate(zip(label_matches, button_matches)):
            value = value.strip()
            if value and value.lower() != "none":
                if "Adoption Category" in label:
                    categories["AdoptionCategory"] = value
                elif "Medical Category" in label:
                    categories["MedicalCategory"] = value
                elif "Behavior Category" in label:
                    categories["BehaviorCategory"] = value
                elif "Volunteer Category" in label:
                    categories["VolunteerCategory"] = value

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
    if not text or text.lower() in ["none", "none assigned", "not assigned", "unassigned", ""]:
        return None

    # Strategy 1: Look for explicit "Case Manager:" pattern
    import re

    case_manager_match = re.search(r"case\s+manager\s*:?\s*([^–\n]+)", text, re.IGNORECASE)
    if case_manager_match:
        name = case_manager_match.group(1).strip()
        if name and name.lower() not in ["none", "none assigned", "not assigned"]:
            return name

    # Strategy 2: If Adoption Category is formatted as "Name – Category", extract name
    # Common pattern: "Jane Doe – Available" or "John Smith – Pending"
    dash_match = re.match(r"^([^–]+?)\s*–\s*.+", text)
    if dash_match:
        name = dash_match.group(1).strip()
        # Validate it looks like a name (has at least one space or is reasonable length)
        if name and len(name) > 2 and name.lower() not in ["none", "not assigned"]:
            return name

    # Strategy 3: If the whole text is just a name (no special formatting), use it
    # But only if it's reasonable (2-50 chars, not all caps acronyms)
    if len(text) >= 2 and len(text) <= 50 and not re.match(r"^[A-Z\s]{3,}$", text):
        # Check if it contains typical name patterns
        if re.search(r"[a-z]", text):  # Has lowercase (not all caps acronym)
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
            ordered = [
                row[k] for k in sorted(row.keys(), key=lambda x: int(x) if x.isdigit() else 0)
            ]
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

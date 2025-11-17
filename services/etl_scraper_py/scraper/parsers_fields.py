"""
Shared HTML parsing helpers and field-level utilities.

Provides composable, pure functions for common HTML parsing patterns
used across all ShelterLuv scraper parsers. These helpers enforce
consistency and reduce code duplication.
"""

from typing import Any, Dict, List, Optional, Tuple
import re
from datetime import datetime


def extract_text_by_selector(page, selector: str, default: str = "") -> str:
    """
    Extract text content from a single element by CSS selector.

    Args:
        page: Playwright page object
        selector: CSS selector string
        default: Default value if element not found

    Returns:
        Extracted text or default value
    """
    try:
        elem = page.locator(selector)
        if elem.count() > 0:
            return elem.first.inner_text(timeout=1000).strip()
        return default
    except Exception:
        return default


def extract_text_by_selectors(page, selectors: List[str], default: str = "") -> str:
    """
    Try multiple selectors in order until one succeeds.

    Args:
        page: Playwright page object
        selectors: List of CSS selector strings to try
        default: Default value if no selector matches

    Returns:
        Extracted text or default value
    """
    for selector in selectors:
        text = extract_text_by_selector(page, selector)
        if text:
            return text
    return default


def extract_attribute_by_selector(page, selector: str, attribute: str, default: str = "") -> str:
    """
    Extract an attribute value from a single element by CSS selector.

    Args:
        page: Playwright page object
        selector: CSS selector string
        attribute: Attribute name to extract
        default: Default value if element/attribute not found

    Returns:
        Attribute value or default
    """
    try:
        elem = page.locator(selector)
        if elem.count() > 0:
            return elem.first.get_attribute(attribute, timeout=1000) or default
        return default
    except Exception:
        return default


def extract_multiple_texts_by_selector(page, selector: str) -> List[str]:
    """
    Extract text from multiple elements matching a selector.

    Args:
        page: Playwright page object
        selector: CSS selector string

    Returns:
        List of extracted text values
    """
    try:
        elements = page.locator(selector)
        texts = []
        for i in range(elements.count()):
            text = elements.nth(i).inner_text(timeout=1000).strip()
            if text:
                texts.append(text)
        return texts
    except Exception:
        return []


def extract_table_rows_as_dicts(page, table_selector: str, header_selectors: List[str]) -> List[Dict[str, str]]:
    """
    Extract table data as list of dictionaries.

    Args:
        page: Playwright page object
        table_selector: CSS selector for table rows
        header_selectors: List of CSS selectors for column headers

    Returns:
        List of dictionaries with column headers as keys
    """
    try:
        rows = page.locator(f"{table_selector} tr")
        results = []

        headers = []
        for header_sel in header_selectors:
            header_text = extract_text_by_selector(page, header_sel)
            headers.append(header_text or f"col_{len(headers)}")

        for i in range(1, rows.count()):  # Skip header row
            row_data = {}
            cells = rows.nth(i).locator("td")
            for j in range(min(cells.count(), len(headers))):
                cell_text = cells.nth(j).inner_text(timeout=1000).strip()
                row_data[headers[j]] = cell_text
            if row_data:
                results.append(row_data)

        return results
    except Exception:
        return []


def normalize_date_string(date_str: str) -> Optional[str]:
    """
    Normalize various date string formats to ISO format.

    Args:
        date_str: Date string to normalize

    Returns:
        ISO formatted date string or None if parsing fails
    """
    if not date_str or date_str.strip() == "":
        return None

    # Common date patterns
    patterns = [
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%m/%d/%Y'),  # MM/DD/YYYY
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),  # YYYY-MM-DD
        (r'(\d{1,2})-(\d{1,2})-(\d{4})', '%m-%d-%Y'),  # MM-DD-YYYY
        (r'(\d{1,2})\s+(\w{3})\s+(\d{4})', '%d %b %Y'),  # DD Mon YYYY
    ]

    for pattern, fmt in patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                dt = datetime.strptime(match.group(0), fmt)
                return dt.date().isoformat()
            except ValueError:
                continue

    # If no pattern matches, return the original string
    return date_str.strip()


def normalize_weight_string(weight_str: str) -> Tuple[Optional[float], str]:
    """
    Normalize weight strings to pounds.

    Args:
        weight_str: Weight string (e.g., "45 lbs", "20.5 kg")

    Returns:
        Tuple of (weight_in_lbs, original_string)
    """
    if not weight_str or weight_str.strip() == "":
        return None, weight_str

    # Extract numeric value
    match = re.search(r'(\d+(?:\.\d+)?)', weight_str)
    if not match:
        return None, weight_str

    weight = float(match.group(1))

    # Check for unit
    if 'kg' in weight_str.lower():
        weight *= 2.20462  # Convert kg to lbs

    return round(weight, 1), weight_str


def clean_html_text(html: str) -> str:
    """
    Clean HTML content to extract readable text.

    Args:
        html: HTML string

    Returns:
        Cleaned text
    """
    if not html:
        return ""

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html)

    # Decode common HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')

    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def split_text_into_sections(text: str, section_delimiters: List[str] = None) -> List[Tuple[str, str]]:
    """
    Split text into sections based on delimiters.

    Args:
        text: Text to split
        section_delimiters: List of delimiter patterns (default: common memo delimiters)

    Returns:
        List of (section_title, section_content) tuples
    """
    if not text:
        return []

    if section_delimiters is None:
        section_delimiters = [
            r'(\d{1,2}/\d{1,2}/\d{4})',  # Dates like MM/DD/YYYY
            r'(\w+ \d{1,2}, \d{4})',     # Dates like "Month DD, YYYY"
            r'([A-Z][^.!?]*:)',          # Title: patterns
            r'(\n\s*[A-Z][A-Z\s]+\n)',  # ALL CAPS section headers
        ]

    sections = []
    current_section = ""
    current_title = "General"

    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if line matches any delimiter pattern
        is_delimiter = any(re.search(pattern, line, re.IGNORECASE) for pattern in section_delimiters)

        if is_delimiter:
            # Save previous section
            if current_section:
                sections.append((current_title, current_section.strip()))

            # Start new section
            current_title = line
            current_section = ""
        else:
            current_section += line + " "

    # Add final section
    if current_section:
        sections.append((current_title, current_section.strip()))

    return sections


def extract_table_rows_by_xpath(page, table_xpath: str, min_cols: int = 2, max_rows: int = 100) -> List[List[str]]:
    """
    Extract table rows as lists of cell text values using XPath.

    This handles the common pattern of finding a table by XPath and extracting
    row data that's used across many medical parsers.

    Args:
        page: Playwright page object
        table_xpath: XPath selector for the table
        min_cols: Minimum number of columns required for a valid row
        max_rows: Maximum number of rows to process

    Returns:
        List of rows, where each row is a list of cell text values
    """
    try:
        table = page.locator(f"xpath={table_xpath}")
        if table.count() == 0:
            return []

        rows = table.locator("tbody tr")
        row_count = min(rows.count(), max_rows)
        result_rows = []

        for i in range(row_count):
            try:
                row = rows.nth(i)
                cells = row.locator("td")
                if cells.count() >= min_cols:
                    cell_texts = []
                    for j in range(cells.count()):
                        cell_text = cells.nth(j).inner_text(timeout=1000).strip()
                        cell_texts.append(cell_text)
                    if cell_texts:  # Only add non-empty rows
                        result_rows.append(cell_texts)
            except Exception:
                continue

        return result_rows
    except Exception:
        return []


def find_table_by_multiple_xpaths(page, xpath_selectors: List[str]) -> Optional[Any]:
    """
    Find a table element using multiple XPath selectors, trying each in order.

    This handles the common pattern where parsers try multiple XPath variations
    to find the same conceptual table element.

    Args:
        page: Playwright page object
        xpath_selectors: List of XPath selectors to try in order

    Returns:
        Table locator if found, None otherwise
    """
    for xpath in xpath_selectors:
        try:
            table = page.locator(f"xpath={xpath}")
            if table.count() > 0:
                return table
        except Exception:
            continue
    return None


def extract_medical_table_data(page, section_name: str, field_mapping: Dict[int, str], min_cols: int = 3) -> List[Dict[str, str]]:
    """
    Generic function for extracting medical table data.

    This handles the common pattern of medical tables with multiple columns
    where each column maps to a specific field name.

    Args:
        page: Playwright page object
        section_name: Name of the medical section (e.g., 'Active Diagnoses')
        field_mapping: Dict mapping column index to field name
        min_cols: Minimum columns required

    Returns:
        List of dictionaries with extracted data
    """
    xpath_selectors = [
        f"//h2[normalize-space()='{section_name}']/following-sibling::table[1]",
        f"//h2[normalize-space()='{section_name}']/following::table[1]",
        f"//h2[contains(text(),'{section_name}')]/following-sibling::table[1]",
        f"//table[preceding::h2[contains(text(),'{section_name}')]][1]"
    ]

    table = find_table_by_multiple_xpaths(page, xpath_selectors)
    if not table:
        return []

    rows = extract_table_rows_by_xpath(page, f"//h2[normalize-space()='{section_name}']/following-sibling::table[1]", min_cols)

    results = []
    for row in rows:
        item = {}
        for col_idx, field_name in field_mapping.items():
            if col_idx < len(row):
                item[field_name] = row[col_idx]
        if item.get(list(field_mapping.values())[0]):  # Only add if primary field has content
            results.append(item)

    return results


def categorize_attributes(attributes: List[str], behavioral_keywords: List[str] = None) -> Dict[str, List[str]]:
    """
    Categorize a list of attributes into behavioral and physical.

    Args:
        attributes: List of attribute strings to categorize
        behavioral_keywords: Keywords that indicate behavioral attributes (optional)

    Returns:
        Dict with 'behavioral' and 'physical' keys containing categorized lists
    """
    if behavioral_keywords is None:
        behavioral_keywords = [
            "compatibility", "energy level", "events", "stairs", "bio",
            "intake notes", "kid", "cat", "dog", "has bio", "has intake",
            "behavior", "behavioral"
        ]

    behavioral = []
    physical = []

    for attr in attributes:
        attr_lower = attr.lower()
        if any(keyword in attr_lower for keyword in behavioral_keywords):
            behavioral.append(attr)
        else:
            physical.append(attr)

    return {
        "behavioral": list(set(behavioral)),  # Remove duplicates
        "physical": list(set(physical))
    }


def clean_attribute_text(text: str) -> str:
    """
    Clean attribute text by removing numbering prefixes and extra whitespace.

    Args:
        text: Raw attribute text

    Returns:
        Cleaned attribute text
    """
    if not text:
        return text

    # Remove numbering prefixes like "1. ", "2. ", etc.
    if ". " in text:
        text = text.split(". ", 1)[1]

    return text.strip()


# Note: The main orchestration function is now in parsers_orchestration.py
# Import it directly when needed to avoid circular imports
"""
Data normalization functions for ETL pipeline.

Handles basic field normalization: age, size, status, arrays.
Separated from enrichment.py to keep file sizes manageable.
"""

from typing import Dict, Any
from datetime import datetime
import re


def normalize_basic_fields(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize basic fields: age, size, status, arrays."""
    result = dict(raw)

    # Normalize Age -> AgeYears + AgeDisplay
    age_value = result.get('Age')

    # If Age came in as a number, convert to string once
    if isinstance(age_value, (int, float)):
        age_value = str(age_value)
        result['Age'] = age_value

    # Always compute AgeYears/AgeDisplay, even if Age is missing/None
    age_years = _normalize_age_years(age_value)  # will return 0.0 on None/invalid
    result['AgeYears'] = age_years
    result['AgeDisplay'] = _build_age_display(age_years)

    # Normalize Size and Status
    if 'Size' in result:
        result['Size'] = _normalize_size(result['Size'])
    if 'Status' in result:
        result['Status'] = _normalize_status(result['Status'])

    # Ensure arrays are lists
    if 'Photos' not in result or not isinstance(result['Photos'], list):
        result['Photos'] = []
    if 'Treatments' not in result or not isinstance(result['Treatments'], list):
        result['Treatments'] = []

    return result


def _normalize_age_years(age_str: str = None) -> float:
    """
    Normalize age string to years as float.

    Args:
        age_str: Age string like "2 years", "1.5 years", "6 months", etc.

    Returns:
        Age in years as float, or 0.0 if invalid/missing
    """
    if not age_str or not isinstance(age_str, str):
        return 0.0

    age_str = age_str.strip().lower()

    # Handle "X years", "X months", "X weeks" patterns
    year_match = re.search(r'(\d+(?:\.\d+)?)\s*years?', age_str)
    month_match = re.search(r'(\d+(?:\.\d+)?)\s*months?', age_str)
    week_match = re.search(r'(\d+(?:\.\d+)?)\s*weeks?', age_str)

    try:
        if year_match:
            return float(year_match.group(1))
        elif month_match:
            return float(month_match.group(1)) / 12.0
        elif week_match:
            return float(week_match.group(1)) / 52.0
        else:
            # Try to parse as plain number (assume years)
            return float(age_str)
    except (ValueError, AttributeError):
        return 0.0


def _build_age_display(age_years: float) -> str:
    """
    Build human-readable age display string.

    Args:
        age_years: Age in years as float

    Returns:
        Display string like "2 years", "1.5 years", "6 months", etc.
    """
    if age_years < 0.1:  # Less than ~1 month
        return "Unknown"

    if age_years < 1.0:
        months = int(round(age_years * 12))
        if months == 1:
            return "1 month"
        else:
            return f"{months} months"

    if age_years < 2.0:
        # Show one decimal for puppies
        return ".1f"

    years = int(age_years)
    if years == 1:
        return "1 year"
    else:
        return f"{years} years"


def _normalize_size(size_str: str = None) -> str:
    """
    Normalize size string to schema enum values.

    Args:
        size_str: Raw size string from API/scraping

    Returns:
        Normalized size or original if no mapping found
    """
    if not size_str or not isinstance(size_str, str):
        return "UNKNOWN"

    size_lower = size_str.lower().strip()

    # Map ShelterLuv formats to schema formats
    # Handle new format like "SMALL (0-24)" and legacy formats
    if 'small' in size_lower:
        if 'x-small' in size_lower or 'extra small' in size_lower:
            return 'Small'  # Schema doesn't have XS, map to Small
        else:
            return 'Small'
    elif 'medium' in size_lower:
        return 'Medium'
    elif 'large' in size_lower:
        if 'x-large' in size_lower or 'extra large' in size_lower or 'xxl' in size_lower:
            return 'X-Large'
        else:
            return 'Large'

    # If no match, indicate unknown rather than guessing
    return 'UNKNOWN'


def _normalize_status(status_str: str = None) -> str:
    """
    Normalize status string to schema enum values.

    Args:
        status_str: Raw status string from API/scraping

    Returns:
        Normalized status or original if no mapping found
    """
    if not status_str or not isinstance(status_str, str):
        return "UNKNOWN"

    status_str = status_str.strip().upper()

    # Common status mappings from ShelterLuv to our schema
    status_mappings = {
        'AVAILABLE': 'AVAILABLE',
        'ADOPTED': 'ADOPTED',
        'PENDING': 'PENDING',
        'HOLD': 'HOLD',
        'NOT AVAILABLE': 'NOT_AVAILABLE',
        'DECEASED': 'DECEASED',
        'TRANSFERRED': 'TRANSFERRED',
        'RETURNED': 'RETURNED',
        # Handle various ShelterLuv formats
        'AVAILABLE FOR ADOPTION': 'AVAILABLE',
        'UNDER ADOPTION': 'PENDING',
        'ON HOLD': 'HOLD',
        # Handle new ShelterLuv formats
        'FOSTER AVAILABLE': 'AVAILABLE',
        'HEADQUARTERS AVAILABLE': 'AVAILABLE',
        'HEADQUARTERS UNAVAILABLE - PENDING MEDICAL RESULTS': 'PENDING',
        'FOSTER UNAVAILABLE - PENDING MEDICAL RESULTS': 'PENDING',
        'FOSTER- PENDING ADOPTION': 'PENDING',
        'HEADQUARTERS AVAILABLE (NOT ONLINE)': 'AVAILABLE',
        'HEADQUARTERS HOSPICE AVAILABLE': 'AVAILABLE',
        'HEADQUARTERS- PENDING ADOPTION': 'PENDING',
        'FOSTER HOSPICE AVAILABLE': 'AVAILABLE',
        'FOSTER AVAILABLE (NOT ONLINE)': 'AVAILABLE',
        'HEADQUARTERS UNAVAILABLE - PENDING BEHAVIORAL ASSESSMENT': 'PENDING'
    }

    return status_mappings.get(status_str, status_str)

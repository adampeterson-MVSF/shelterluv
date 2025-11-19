"""
Data normalization functions for ETL pipeline.

Handles basic field normalization: age, size, status, arrays.
Separated from enrichment.py to keep file sizes manageable.
"""

import re
from datetime import datetime
from typing import Any, Dict

from dog_schema import _normalize_status as normalize_status_from_schema


def normalize_basic_fields(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize basic fields: age, size, status, arrays."""
    result = dict(raw)

    # Normalize Age -> AgeYears + AgeDisplay
    age_value = result.get("Age")

    # If Age came in as a number, convert to string once
    if isinstance(age_value, (int, float)):
        age_value = str(age_value)
        result["Age"] = age_value

    # Compute AgeYears/AgeDisplay if not already present or if Age field exists
    existing_age_years = result.get("AgeYears")
    if existing_age_years is None or age_value is not None:
        age_years = _normalize_age_years(age_value)  # will return 0.0 on None/invalid
        result["AgeYears"] = age_years
        result["AgeDisplay"] = _build_age_display(age_years)

    # Normalize Size and Status
    if "Size" in result:
        result["Size"] = _normalize_size(result["Size"])
    if "Status" in result:
        result["Status"] = normalize_status_from_schema(result["Status"])

    # Ensure arrays are lists - ETL owns all shape defaults for schema-defined arrays
    array_fields = ["Photos", "Treatments", "Attributes", "BehavioralAttributes", "PhysicalAttributes"]
    for field in array_fields:
        if field not in result or not isinstance(result[field], list):
            result[field] = []

    return result


def _normalize_age_years(age_str: str = None) -> float:
    """
    Normalize age string to years as float.

    Args:
        age_str: Age string like "2 years", "1.5 years", "6 months", etc.
                 If a pure number (e.g., "101"), ShelterLuv is giving us months.

    Returns:
        Age in years as float, or 0.0 if invalid/missing
    """
    if not age_str or not isinstance(age_str, str):
        return 0.0

    age_str = age_str.strip().lower()

    # Handle "X years", "X months", "X weeks" patterns
    year_match = re.search(r"(\d+(?:\.\d+)?)\s*years?", age_str)
    month_match = re.search(r"(\d+(?:\.\d+)?)\s*months?", age_str)
    week_match = re.search(r"(\d+(?:\.\d+)?)\s*weeks?", age_str)

    try:
        if year_match:
            return float(year_match.group(1))
        elif month_match:
            return float(month_match.group(1)) / 12.0
        elif week_match:
            return float(week_match.group(1)) / 52.0
        else:
            # Handle compact "8Y/5M/4D" and variants like "8y/5m", "8y 5m"
            compact_match = re.fullmatch(
                r"\s*(\d+)\s*y(?:[/\s]+(\d+)\s*m)?(?:[/\s]+(\d+)\s*d)?\s*", age_str, flags=re.I
            )
            if compact_match:
                years = int(compact_match.group(1))
                months = int(compact_match.group(2) or 0)
                # days are ignored for years calc; you could add + days/365 if desired
                return round(years + months / 12.0, 1)

            # Pure numeric string (no units) - ShelterLuv gives us months
            # e.g., "101" means 101 months, not 101 years
            if age_str.replace(".", "").isdigit():
                months_float = float(age_str)
                return round(months_float / 12.0, 1) if months_float > 0 else 0.0
            # Try to parse as plain number (fallback for edge cases)
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
        return f"{age_years:.1f} years"

    years = int(age_years)
    if years == 1:
        return "1 year"
    else:
        return f"{years} years"


# Size normalization mapping (data-driven)
SIZE_MAPPING = {
    "Small": ["small", "x-small", "extra small"],
    "Medium": ["medium"],
    "Large": ["large"],
    "X-Large": ["x-large", "extra large", "xxl"]
}

def _normalize_size(size_str: str = None) -> str:
    """
    Normalize size string to schema enum values using data-driven mapping.

    Args:
        size_str: Raw size string from API/scraping

    Returns:
        Normalized size or "UNKNOWN" if no mapping found
    """
    if not size_str or not isinstance(size_str, str):
        return "UNKNOWN"

    size_lower = size_str.lower().strip()

    # Check each size category for matches
    for normalized_size, keywords in SIZE_MAPPING.items():
        if any(keyword in size_lower for keyword in keywords):
            return normalized_size

    # If no match, indicate unknown rather than guessing
    return "UNKNOWN"

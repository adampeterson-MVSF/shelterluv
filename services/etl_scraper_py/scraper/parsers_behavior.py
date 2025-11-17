"""
Behavior field parsing functions for ShelterLuv scraper.
Handles behavior assessments, plans, playgroups, and checks.
Prefers structured data, falls back to HTML parsing.
"""

from typing import Any, Dict, List

from .navigation import SELECTORS


def parse_behavior_from_raw_record(raw_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract behavior information from a canonical raw animal record.

    Args:
        raw_record: Canonical raw animal record with structured behavior data.

    Returns:
        Dict with behavior fields like BehaviorPlan, BehaviorAssessment, etc.
    """
    # For now, this is a placeholder - behavior data often comes from tab scraping
    # rather than being part of the initial record structure
    return {}


def scrape_behavioral_fields(navigation) -> Dict[str, str]:
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


def parse_behavioral_attributes(attributes_list: List[str]) -> Dict[str, List[str]]:
    """
    Parse and categorize behavioral attributes from a list of attribute strings.

    Args:
        attributes_list: List of attribute strings (e.g., ["Good with cats", "High energy", ...])

    Returns:
        Dict with 'behavioral' and 'physical' keys containing categorized attributes.
    """
    behavioral_keywords = [
        "compatibility",
        "energy level",
        "events",
        "stairs",
        "bio",
        "intake notes",
        "kid",
        "cat",
        "dog",
        "has bio",
        "has intake",
    ]

    behavioral = []
    physical = []

    for attr in attributes_list:
        attr_lower = attr.lower()
        if any(keyword in attr_lower for keyword in behavioral_keywords):
            behavioral.append(attr)
        else:
            physical.append(attr)

    return {"behavioral": behavioral, "physical": physical}


def extract_behavioral_keywords_from_memos(memos_text: str) -> Dict[str, str]:
    """
    Extract behavioral information from memo text.

    Args:
        memos_text: Raw memo text content.

    Returns:
        Dict with behavioral fields extracted from memos.
    """
    result = {}

    if not memos_text:
        return result

    memos_lower = memos_text.lower()

    # Look for behavioral assessment patterns
    if "behavior" in memos_lower:
        # Extract behavioral assessment sections
        # This is a simplified extraction - could be enhanced with more specific patterns
        result["BehaviorAssessment"] = memos_text

    # Look for playgroup information
    if "playgroup" in memos_lower:
        result["BehaviorPlaygroups"] = memos_text

    return result

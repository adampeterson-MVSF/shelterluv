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


def extract_behavioral_assessments(page) -> List[Dict[str, Any]]:
    """Extract structured behavioral assessments from the behavioral section."""
    assessments = []

    try:
        # Look for behavioral assessment sections
        assessment_selectors = [
            ".behavioral-assessments",
            "[data-section='behavioral'] .assessment",
            ".behavior .assessment",
            "[id*='behavior'] .assessment"
        ]

        for section_sel in assessment_selectors:
            try:
                assessment_elements = page.locator(f"{section_sel}").all()
                for element in assessment_elements:
                    try:
                        # Extract assessment details
                        assessment_data = _extract_single_behavioral_assessment(element)
                        if assessment_data:
                            assessments.append(assessment_data)

                    except Exception:
                        continue

                if assessments:
                    break

            except Exception:
                continue

        # Also check for behavioral plans section
        plan_selectors = [
            ".behavior-plans",
            "[data-section='behavioral'] .plan",
            ".behavior .plan"
        ]

        for plan_sel in plan_selectors:
            try:
                plan_elements = page.locator(f"{plan_sel}").all()
                for element in plan_elements:
                    try:
                        plan_data = _extract_behavioral_plan(element)
                        if plan_data:
                            assessments.append(plan_data)

                    except Exception:
                        continue

            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting behavioral assessments: {e}")

    return assessments


def _extract_single_behavioral_assessment(element) -> Dict[str, Any]:
    """Extract a single behavioral assessment from an element."""
    try:
        # Try to find assessment type, date, assessor, etc.
        assessment = {
            "assessment_type": "",
            "date": "",
            "assessor": "",
            "results": "",
            "recommendations": ""
        }

        # Look for headers or titles
        title_element = element.locator("h3, h4, .title, .assessment-type").first
        if title_element.count() > 0:
            assessment["assessment_type"] = title_element.inner_text(timeout=1000).strip()

        # Look for date information
        date_selectors = ["[data-date]", ".date", "time", "[datetime]"]
        for date_sel in date_selectors:
            try:
                date_element = element.locator(date_sel).first
                if date_element.count() > 0:
                    assessment["date"] = date_element.inner_text(timeout=1000).strip()
                    break
            except Exception:
                continue

        # Look for assessor information
        assessor_selectors = [".assessor", ".by", "[data-assessor]"]
        for assessor_sel in assessor_selectors:
            try:
                assessor_element = element.locator(assessor_sel).first
                if assessor_element.count() > 0:
                    assessment["assessor"] = assessor_element.inner_text(timeout=1000).strip()
                    break
            except Exception:
                continue

        # Extract content as results
        content_selectors = [".content", ".results", ".assessment-content", "p"]
        content_parts = []
        for content_sel in content_selectors:
            try:
                content_elements = element.locator(content_sel).all()
                for content_el in content_elements:
                    text = content_el.inner_text(timeout=1000).strip()
                    if text:
                        content_parts.append(text)
            except Exception:
                continue

        assessment["results"] = " ".join(content_parts)

        # If we have meaningful data, return the assessment
        if assessment["assessment_type"] or assessment["results"]:
            return assessment

    except Exception:
        pass

    return None


def _extract_behavioral_plan(element) -> Dict[str, Any]:
    """Extract a behavioral plan from an element."""
    try:
        plan = {
            "assessment_type": "Behavioral Plan",
            "date": "",
            "assessor": "",
            "results": "",
            "recommendations": ""
        }

        # Extract plan content
        content_element = element.locator(".content, .plan-content, p").first
        if content_element.count() > 0:
            plan["recommendations"] = content_element.inner_text(timeout=1000).strip()

        # Look for date/assessor info
        meta_element = element.locator(".meta, .info, small").first
        if meta_element.count() > 0:
            meta_text = meta_element.inner_text(timeout=1000).strip()
            # Simple parsing - could be enhanced
            if "by" in meta_text.lower():
                parts = meta_text.split("by")
                if len(parts) > 1:
                    plan["assessor"] = parts[1].strip()

        if plan["recommendations"]:
            return plan

    except Exception:
        pass

    return None

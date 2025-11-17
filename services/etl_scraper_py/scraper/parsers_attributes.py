"""
Attributes and behavioral parsing functions for ShelterLuv scraper.

Handles extraction of behavioral attributes, physical attributes, and disclaimers.
"""

from typing import Any, Dict


def _extract_attributes_disclaimers(page, result: Dict[str, Any]) -> None:
    """Extract behavioral & physical attributes from Disclaimers section."""
    try:
        # Container
        container_xpath = "//h1[normalize-space()='Disclaimers']/ancestor::div[@class='border-y-2 border-gray-100']/following-sibling::div[1]"
        container_elem = page.locator(f"xpath={container_xpath}")
        if container_elem.count() == 0:
            return

        container = container_elem.first

        # Each attribute card
        cards_xpath = ".//div[contains(@class,'text-xs leading-4 border-l-8')]"
        card_elems = container.locator(f"xpath={cards_xpath}")

        behavioral_attrs = []
        physical_attrs = []

        for i in range(card_elems.count()):
            try:
                card = card_elems.nth(i)

                # Get h3 text (attribute title)
                h3_elem = card.locator(".//h3")
                if h3_elem.count() > 0:
                    attr_text = h3_elem.first.inner_text(timeout=1000).strip()

                    # Remove ordering index (e.g., "1. " -> "")
                    if ". " in attr_text:
                        attr_text = attr_text.split(". ", 1)[1]

                    # Categorize as behavioral or physical
                    attr_lower = attr_text.lower()
                    if any(keyword in attr_lower for keyword in [
                        'compatibility', 'energy level', 'events', 'stairs',
                        'kid', 'cat', 'dog', 'has bio', 'has intake', 'behavior'
                    ]):
                        behavioral_attrs.append(attr_text)
                    else:
                        physical_attrs.append(attr_text)

            except Exception:
                continue

        result["BehavioralAttributes"] = behavioral_attrs
        result["PhysicalAttributes"] = physical_attrs
        result["Attributes"] = behavioral_attrs + physical_attrs

    except Exception as e:
        print(f"Error extracting attributes from disclaimers: {e}")


def _derive_categories_from_attributes(result: Dict[str, Any]) -> None:
    """Derive categories based on attributes present."""
    try:
        attributes = result.get("Attributes", [])
        if not attributes:
            return

        # Category mapping based on attribute keywords
        category_mappings = {
            "cats": ["cat", "cats", "feline"],
            "dogs": ["dog", "dogs", "canine"],
            "children": ["kid", "kids", "child", "children"],
            "energy": ["high energy", "low energy", "energy level"],
            "special_needs": ["special needs", "medical", "handicap"],
        }

        derived_categories = []

        for attr in attributes:
            attr_lower = attr.lower()
            for category, keywords in category_mappings.items():
                if any(keyword in attr_lower for keyword in keywords):
                    if category not in derived_categories:
                        derived_categories.append(category)

        if derived_categories:
            result["DerivedCategories"] = derived_categories

    except Exception as e:
        print(f"Error deriving categories from attributes: {e}")

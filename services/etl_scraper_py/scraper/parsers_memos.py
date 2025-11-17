"""
Field-level parsing functions for memo and note information.
Handles latest memos, medical memos, and memo history.
"""

from typing import Any, Dict, List

from .navigation import SELECTORS


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


def extract_memos_section(page, result: Dict[str, Any]) -> None:
    """Extract memos section from the main profile page."""
    try:
        # Look for memos section in the main content
        memos_section = page.locator('text="Memos"').locator('xpath=following-sibling::*[1]')
        if memos_section.count() > 0:
            memos_text = memos_section.first.inner_text(timeout=3000)
            if memos_text.strip():
                result["Memos"] = memos_text.strip()
    except Exception:
        # Memos are optional
        pass


def scrape_memos_page(page, internal_id: str) -> str:
    """Scrape the dedicated memos page for a specific animal."""
    try:
        # Navigate to memos page if not already there
        page.goto(f"/animal/{internal_id}/memos", wait_until="networkidle")

        # Wait for content to load
        page.wait_for_selector('text="Memos"', timeout=5000)

        # Extract all memo content
        memo_elements = page.locator('[data-testid="memo-item"], .memo-item, .memo')
        if memo_elements.count() > 0:
            memos = []
            for i in range(memo_elements.count()):
                memo_text = memo_elements.nth(i).inner_text(timeout=2000).strip()
                if memo_text:
                    memos.append(memo_text)

            return "\n\n".join(memos)
        else:
            # Fallback: get all text from memos section
            memos_section = page.locator('text="Memos"').locator('xpath=ancestor-or-self::*[contains(@class, "memos") or contains(@id, "memos")]')
            if memos_section.count() > 0:
                return memos_section.first.inner_text(timeout=3000).strip()

    except Exception as e:
        # Log error but don't fail the entire scrape
        print(f"Warning: Could not scrape memos page for {internal_id}: {e}")

    return ""


def _extract_memos_section(page, result: Dict[str, Any]) -> None:
    """Extract memos section content."""
    try:
        # Look for memo cards anywhere on the page - they have the characteristic styling
        # Try multiple approaches to find memo content

        memo_sections = {
            "Foster Notes": [],
            "Kennel Card / Website Memo": [],
            "Medical": [],
            "Disclaimer": [],
            "Case Manager Notes": [],
            "Pop-up": []
        }

        # Method 1: Look for cards under an H1 "Memos" section (original approach)
        container_xpath = "//h1[normalize-space()='Memos']/ancestor::div[@class='border-y-2 border-gray-100']/following-sibling::div[1]"
        container_elem = page.locator(f"xpath={container_xpath}")
        if container_elem.count() > 0:
            container = container_elem.first
            cards_xpath = ".//div[contains(@class,'text-xs leading-4 border-l-8')]"
            card_elems = container.locator(f"xpath={cards_xpath}")
        else:
            # Method 2: Look for memo cards anywhere on the page (fallback)
            # Memo cards have the class 'text-xs leading-4 border-l-8'
            card_elems = page.locator("xpath=//div[contains(@class,'text-xs leading-4 border-l-8')]")

        for i in range(card_elems.count()):
            try:
                card = card_elems.nth(i)

                # Memo type from h3 - use XPath syntax properly
                h3_elem = card.locator("xpath=.//h3")
                memo_type = ""
                if h3_elem.count() > 0:
                    memo_type = h3_elem.first.inner_text(timeout=1000).strip()

                # Memo body text - use XPath syntax properly
                body_elem = card.locator("xpath=.//div[@class='text-sm text-black']/p")
                memo_body = ""
                if body_elem.count() > 0:
                    # Get all p elements and join their text
                    body_texts = []
                    for j in range(body_elem.count()):
                        text = body_elem.nth(j).inner_text(timeout=1000).strip()
                        if text:
                            body_texts.append(text)
                    memo_body = "\n".join(body_texts)

                # Add to appropriate section
                if memo_type in memo_sections:
                    if memo_body:
                        memo_sections[memo_type].append(memo_body)

            except Exception:
                continue

        # Combine memo sections
        all_memos = []
        for memo_type, contents in memo_sections.items():
            if contents:
                section_text = f"{memo_type}:\n" + "\n\n".join(contents)
                all_memos.append(section_text)

        result["MemosRawHTML"] = "\n\n".join(all_memos)

        # Extract structured notes
        personality_notes = []
        intake_notes = []
        medical_notes = []

        # Foster Notes -> PersonalityNotes
        if "Foster Notes" in memo_sections:
            personality_notes.extend(memo_sections["Foster Notes"])

        # Medical memos -> MedicalNotes
        if "Medical" in memo_sections:
            medical_notes.extend(memo_sections["Medical"])

        # Kennel Card / Website Memo -> Description/Bio
        if "Kennel Card / Website Memo" in memo_sections:
            personality_notes.extend(memo_sections["Kennel Card / Website Memo"])

        # Disclaimer memos often contain intake notes
        if "Disclaimer" in memo_sections:
            for disclaimer in memo_sections["Disclaimer"]:
                disclaimer_lower = disclaimer.lower()
                if "intake notes:" in disclaimer_lower or "intake" in disclaimer_lower:
                    intake_notes.append(disclaimer)
                else:
                    # Other disclaimers might be personality-related
                    personality_notes.append(disclaimer)

        result["PersonalityNotes"] = "\n\n".join(personality_notes) if personality_notes else "Not Available"
        result["IntakeNotes"] = "\n\n".join(intake_notes) if intake_notes else ""
        result["MedicalNotes"] = "\n\n".join(medical_notes) if medical_notes else "Not Available"

    except Exception as e:
        print(f"Error extracting memos section: {e}")
        import traceback
        traceback.print_exc()

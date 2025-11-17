"""
Photos and attributes parsing functions for ShelterLuv scraper.
Handles photo URLs, document files, and attribute categorization.
Prefers structured data, falls back to HTML parsing.
"""

from typing import Any, Dict, List

from .navigation import SELECTORS


def parse_photos_from_raw_record(raw_record: Dict[str, Any]) -> List[str]:
    """
    Extract photo URLs from a canonical raw animal record.

    Args:
        raw_record: Canonical raw animal record with photo data.

    Returns:
        List of photo URLs.
    """
    photos = []

    # Try structured photo data first
    if 'photos' in raw_record:
        photos.extend(raw_record['photos'])

    # Fallback to HTML extraction if needed
    html_content = raw_record.get('html_content', '')
    if html_content and not photos:
        photos.extend(extract_photo_urls_from_html(html_content))

    return photos


def extract_photo_urls_from_html(html_content: str) -> List[str]:
    """
    Extract photo URLs from HTML content.

    Args:
        html_content: Raw HTML string.

    Returns:
        List of photo URLs found in the HTML.
    """
    import re

    photos = []

    # Look for profile-pictures URLs (common pattern in ShelterLuv)
    profile_photo_pattern = r'profile-pictures/[^"\'\s]+\.(?:jpg|jpeg|png|gif|webp)'
    matches = re.findall(profile_photo_pattern, html_content, re.IGNORECASE)

    for match in matches:
        # Construct full URL if it's a relative path
        if not match.startswith('http'):
            match = f"https://new.shelterluv.com/{match}"
        if match not in photos:
            photos.append(match)

    # Also look for img src attributes
    img_pattern = r'<img[^>]+src=["\']([^"\']*profile-pictures[^"\']*)["\'][^>]*>'
    img_matches = re.findall(img_pattern, html_content, re.IGNORECASE)

    for img_src in img_matches:
        if not img_src.startswith('http'):
            img_src = f"https://new.shelterluv.com/{img_src}"
        if img_src not in photos:
            photos.append(img_src)

    return photos


def scrape_attributes_from_page(page, navigation) -> Dict[str, List[str]]:
    """
    Scrape behavioral and physical attributes from the profile page.

    Args:
        page: Playwright page object.
        navigation: Navigation helper instance.

    Returns:
        Dict with 'behavioral' and 'physical' keys containing attribute lists.
    """
    from .parsers_fields import categorize_attributes, clean_attribute_text

    try:
        # Wait for dynamic content to load
        page.wait_for_timeout(2000)

        # Try to get attributes from wire:key elements first
        attributes = _extract_attributes_from_wire_keys(page)

        # If no wire:key elements found, try fallback extraction
        if not attributes:
            attributes = _scrape_attributes_fallback(page, navigation)

        # Clean and categorize the attributes
        cleaned_attributes = [clean_attribute_text(attr) for attr in attributes if attr]
        return categorize_attributes(cleaned_attributes)

    except Exception as e:
        print(f"Error scraping attributes from page: {e}")
        return {"behavioral": [], "physical": []}


def _extract_attributes_from_wire_keys(page) -> List[str]:
    """
    Extract attributes from elements with wire:key selectors.

    Returns:
        List of raw attribute text strings
    """
    attributes = []

    # Get both behavioral and physical attribute elements
    behave_elements = page.locator('[wire\\:key^="behave-attr-"]')
    phys_elements = page.locator('[wire\\:key^="phys-attr-"]')

    all_elements = []
    # Collect all elements
    for i in range(behave_elements.count()):
        all_elements.append(behave_elements.nth(i))
    for i in range(phys_elements.count()):
        all_elements.append(phys_elements.nth(i))

    # Extract text from each element
    for elem in all_elements:
        try:
            p_tag = elem.locator("p")
            if p_tag.count() > 0:
                txt = p_tag.inner_text(timeout=500).strip()
                if txt and len(txt) > 3:  # Attributes should be meaningful text
                    attributes.append(txt)
        except Exception:
            continue

    return attributes


def _scrape_attributes_fallback(page, navigation) -> List[str]:
    """
    Fallback method to scrape attributes when wire:key elements are not found.

    Args:
        page: Playwright page object
        navigation: Navigation helper instance

    Returns:
        List of raw attribute text strings
    """
    try:
        # Find the attributes section by looking for the header "Attributes"
        attributes_header = page.locator('p:has-text("Attributes")')
        if attributes_header.count() == 0:
            return []

        # Get the parent div that contains the attributes section
        attributes_section = attributes_header.locator(
            'xpath=ancestor::div[contains(@class, "rounded-lg")]'
        )
        if attributes_section.count() == 0:
            return []

        # Look for badge-like elements within this section
        badge_elements = attributes_section.locator('div[class*="inline-flex"]')
        values = []

        for i in range(badge_elements.count()):
            try:
                elem = badge_elements.nth(i)
                p_tag = elem.locator("p")
                if p_tag.count() > 0:
                    txt = p_tag.inner_text(timeout=500).strip()
                    if txt and len(txt) > 3 and not txt.startswith("This will"):
                        values.append(txt)
            except Exception:
                continue

        return values

    except Exception as e:
        print(f"Error in attributes fallback scraping: {e}")
        return []



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


def _extract_photos_documents(page, result: Dict[str, Any]) -> None:
    """Extract photos and documents from right-hand column."""
    try:
        # Find all profile images - use the most comprehensive approach
        # Look for images with profile-pictures in src (covers both main photo and gallery)
        photos_xpath = "//img[contains(@src, 'profile-pictures')]"
        photo_elems = page.locator(f"xpath={photos_xpath}")
        for i in range(photo_elems.count()):
            try:
                photo_url = photo_elems.nth(i).get_attribute("src", timeout=1000)
                if photo_url and photo_url not in result["Photos"]:
                    result["Photos"].append(photo_url)
            except Exception:
                continue

        # Documents list (file name + URL + date)
        docs_xpath = "//h4[normalize-space()='Documents']/following::div[1]//div[@class='flex justify-between items-center text-sm border-b border-gray-200 pb-1']"
        doc_elems = page.locator(f"xpath={docs_xpath}")
        for i in range(doc_elems.count()):
            try:
                doc_elem = doc_elems.nth(i)

                # Document URL
                url_elem = doc_elem.locator(".//a/@href")
                doc_url = ""
                if url_elem.count() > 0:
                    doc_url = url_elem.first.get_attribute("href", timeout=1000) or ""

                # Document title
                title_elem = doc_elem.locator(".//a")
                doc_title = ""
                if title_elem.count() > 0:
                    doc_title = title_elem.first.inner_text(timeout=1000).strip()

                # Document date
                date_elem = doc_elem.locator(".//div[@class='text-black']")
                doc_date = ""
                if date_elem.count() > 0:
                    doc_date = date_elem.first.inner_text(timeout=1000).strip()

                if doc_title or doc_url:
                    result["Files"].append({
                        "Name": doc_title,
                        "URL": doc_url,
                        "Date": doc_date,
                        "Type": "Document"
                    })

            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting photos and documents: {e}")

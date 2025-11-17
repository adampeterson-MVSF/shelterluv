"""
Media parsing functions for ShelterLuv scraper.

Handles extraction of photos and documents from animal profiles.
"""

from typing import Any, Dict


def _extract_photos_documents(page, result: Dict[str, Any]) -> None:
    """Extract photos and documents from the animal profile."""
    try:
        # Photos section
        photo_selectors = [
            "img[alt*='photo']",
            "img[class*='photo']",
            ".animal-photo img",
            "[data-testid*='photo'] img",
        ]

        for selector in photo_selectors:
            try:
                photos = page.locator(selector)
                count = photos.count()
                for i in range(min(count, 20)):  # Limit to reasonable number
                    try:
                        src = photos.nth(i).get_attribute("src", timeout=1000)
                        if src and src not in result["Photos"]:
                            result["Photos"].append(src)
                    except Exception:
                        continue
            except Exception:
                continue

        # Document files section
        document_selectors = [
            "a[href*='.pdf']",
            "a[href*='.doc']",
            "a[href*='.jpg']",
            "a[href*='.png']",
            "[data-testid*='document'] a",
            "[class*='document'] a",
        ]

        for selector in document_selectors:
            try:
                docs = page.locator(selector)
                count = docs.count()
                for i in range(min(count, 10)):  # Limit to reasonable number
                    try:
                        href = docs.nth(i).get_attribute("href", timeout=1000)
                        text = docs.nth(i).inner_text(timeout=1000).strip()
                        if href and text:
                            doc_info = {
                                "url": href,
                                "name": text,
                                "type": _guess_document_type(href, text)
                            }
                            if doc_info not in result["Files"]:
                                result["Files"].append(doc_info)
                    except Exception:
                        continue
            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting photos and documents: {e}")


def _guess_document_type(url: str, name: str) -> str:
    """Guess document type from URL and name."""
    url_lower = url.lower()
    name_lower = name.lower()

    if '.pdf' in url_lower or '.pdf' in name_lower:
        return 'pdf'
    elif '.doc' in url_lower or '.docx' in url_lower or 'word' in name_lower:
        return 'document'
    elif '.jpg' in url_lower or '.jpeg' in url_lower or '.png' in url_lower:
        return 'image'
    elif 'vaccination' in name_lower or 'vaccine' in name_lower:
        return 'vaccination_record'
    elif 'medical' in name_lower or 'health' in name_lower:
        return 'medical_record'
    elif 'contract' in name_lower or 'agreement' in name_lower:
        return 'contract'
    else:
        return 'document'

"""
Memo parsing and categorization functions for ShelterLuv scraper.

Handles extraction and categorization of memo content from HTML.
"""

import re
from typing import Any, Dict, List

# Keyword sets for memo categorization (pattern-driven)
PERSONALITY_KEYWORDS = [
    "personality",
    "behavior",
    "temperament",
    "disposition",
    "playful",
    "friendly",
    "shy",
    "aggressive",
    "social",
    "anxious",
    "calm",
    "energy",
]

INTAKE_KEYWORDS = [
    "intake",
    "background",
    "history",
    "came from",
    "owner surrender",
    "stray",
    "rescued",
    "previous",
    "origin",
]

MEDICAL_KEYWORDS = [
    "medical",
    "health",
    "vet",
    "treatment",
    "medication",
    "surgery",
    "vaccine",
    "illness",
    "condition",
    "diagnosis",
    "exam",
    "test",
]

# Table-driven memo type definitions
MEMO_TYPES = [
    ("PersonalityNotes", PERSONALITY_KEYWORDS),
    ("IntakeNotes", INTAKE_KEYWORDS),
    ("MedicalNotes", MEDICAL_KEYWORDS),
]


def parse_memos_by_type_pure(memos_html: str) -> Dict[str, str]:
    """
    Parse raw HTML memos into categorized notes by type.
    Returns dict with PersonalityNotes, IntakeNotes, MedicalNotes.

    Pure function that wires together clean_memo_html, split_text_into_sections,
    and categorize_section building blocks.

    Also recognizes "Kennel Card / Website Memo" headers and categorizes them as personality notes.
    """
    text = clean_memo_html(memos_html)
    sections = split_memo_into_sections(text)

    personality_sections = []
    intake_sections = []
    medical_sections = []

    for section in sections:
        section_clean = section.strip()
        if not section_clean or len(section_clean) < 10:  # Skip empty/short sections
            continue

        # Check for "Kennel Card / Website Memo" header - always categorize as personality
        section_lower = section_clean.lower()
        if "kennel card" in section_lower or "website memo" in section_lower:
            # Extract content after the header
            lines = section_clean.split("\n")
            content_lines = []
            found_header = False
            for line in lines:
                if "kennel card" in line.lower() or "website memo" in line.lower():
                    found_header = True
                    # Skip the header line itself, but include content after it
                    continue
                if found_header or not any(keyword in line.lower() for keyword in ["kennel card", "website memo"]):
                    content_lines.append(line)

            if content_lines:
                content = "\n".join(content_lines).strip()
                if content:
                    personality_sections.append(content)
            continue

        # Categorize section by type using table-driven approach
        section_type = categorize_section(section_clean)
        if section_type == "medical":
            medical_sections.append(section_clean)
        elif section_type == "intake":
            intake_sections.append(section_clean)
        elif section_type == "personality":
            personality_sections.append(section_clean)

    return {
        "PersonalityNotes": "\n\n".join(personality_sections) if personality_sections else "Not Available",
        "IntakeNotes": "\n\n".join(intake_sections) if intake_sections else "",
        "MedicalNotes": "\n\n".join(medical_sections) if medical_sections else "Not Available",
    }


def clean_memo_html(html: str) -> str:
    """Clean HTML from memo content, preserving line breaks."""
    from html import unescape

    # Strip HTML tags but preserve line breaks
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return unescape(text)


def split_memo_into_sections(clean_html: str) -> List[str]:
    """Split memo text into sections by timestamps and headers."""
    # Split on timestamps, double newlines, or explicit headers
    sections = re.split(r"\n\s*\n|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}", clean_html)

    # If no sections created, treat entire text as one section
    if not sections or (len(sections) == 1 and not sections[0].strip()):
        sections = [clean_html]

    return sections


def categorize_section(section: str) -> str:
    """
    Categorize a memo section by keyword matching.
    Returns 'medical', 'intake', 'personality', or empty string.

    Priority: medical > intake > personality (medical has highest priority)
    """
    section_lower = section.lower().strip()

    # Get keyword counts for each category using table-driven approach
    counts = {}
    for memo_type, keywords in MEMO_TYPES:
        key = memo_type.lower().replace("notes", "")
        counts[key] = _count_keywords_pure(section_lower, keywords)

    # Return category with most matches (ties: medical > intake > personality)
    medical_count = counts.get("medical", 0)
    intake_count = counts.get("intake", 0)
    personality_count = counts.get("personality", 0)

    if medical_count > 0 and medical_count >= intake_count and medical_count >= personality_count:
        return "medical"
    elif intake_count > 0 and intake_count >= personality_count:
        return "intake"
    elif personality_count > 0:
        return "personality"

    return ""


def _count_keywords_pure(text: str, keywords: List[str]) -> int:
    """Count how many keywords appear in text."""
    return sum(1 for keyword in keywords if keyword in text)


# Backward compatibility: keep old function names that delegate to new ones
def _clean_memo_html_pure(memos_html: str) -> str:
    """Backward compatibility wrapper."""
    return clean_memo_html(memos_html)


def _split_memo_into_sections_pure(text: str) -> List[str]:
    """Backward compatibility wrapper."""
    return split_memo_into_sections(text)


def _categorize_memo_section_pure(section_lower: str) -> str:
    """Backward compatibility wrapper."""
    return categorize_section(section_lower)
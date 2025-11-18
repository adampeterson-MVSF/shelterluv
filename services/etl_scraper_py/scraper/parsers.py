"""
Data parsing and extraction for ShelterLuv scraper.

Handles extraction of structured data from scraped HTML content.
Pure memo parsing functions and record assembly orchestrator.
"""
from typing import Dict

# Import all functions from specialized modules for backward compatibility
from .parsers_memos import (
    parse_memos_by_type_pure,
    clean_memo_html,
    split_memo_into_sections,
    categorize_section,
    _clean_memo_html_pure,
    _split_memo_into_sections_pure,
    _categorize_memo_section_pure,
    _count_keywords_pure,
    PERSONALITY_KEYWORDS,
    INTAKE_KEYWORDS,
    MEDICAL_KEYWORDS,
)
from .parsers_record_summary import ShelterLuvRecordSummaryParsers

# Backward compatibility alias
ShelterLuvParsers = ShelterLuvRecordSummaryParsers


def parse_memos_by_type_pure(memos_html: str) -> Dict[str, str]:
        """
        Parse raw HTML memos into categorized notes by type.
        Returns dict with PersonalityNotes, IntakeNotes, MedicalNotes.
        Delegates to pure function.
        """
        from .parsers_memos import parse_memos_by_type_pure as _parse_memos
        return _parse_memos(memos_html)

"""
Field-level parsing functions for ShelterLuv scraper.

DEPRECATED: This module has been split into domain-specific parsers.
Use parsers_orchestration.py for the main scraping function.
Functions have been moved to:
- Basic info -> parsers_basic_info.py
- Profile -> parsers_profile.py
- Media -> parsers_media.py
- Attributes -> parsers_attributes.py
- Memos -> parsers_memos.py
- Medical -> parsers_medical_detailed.py
- Orchestration -> parsers_orchestration.py
"""

# Re-export the main orchestration function for backward compatibility
from .parsers_orchestration import scrape_animal_record_summary_comprehensive
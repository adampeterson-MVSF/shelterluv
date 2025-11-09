"""
Split ShelterLuv scraper modules.

Combines session, navigation, and parsing modules for backward compatibility.
"""

from typing import Dict, Any
from .session import ShelterLuvSession
from .navigation import ShelterLuvNavigation, SELECTORS
from .parsers import ShelterLuvParsers


class ShelterLuvScraper:
    """
    A context-managed scraper for ShelterLuv data extraction.

    This combines the split modules (session, navigation, parsers) for backward compatibility.
    """

    def __init__(self, username: str, password: str):
        self.session = ShelterLuvSession(username, password)
        self.navigation = None
        self.parsers = None

    def __enter__(self):
        """Initialize browser and login."""
        self.session.__enter__()
        self.navigation = ShelterLuvNavigation(self.session.page)
        self.parsers = ShelterLuvParsers(self.session.page, self.navigation)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up browser resources."""
        self.session.__exit__(exc_type, exc_val, exc_tb)

    def close(self):
        """Legacy close method for backward compatibility."""
        self.session.close()

    def scrape_profile_only(self, animal_id: str) -> Dict[str, Any]:
        """
        Scrape only the main animal profile page (no memos page).
        Returns dict with profile data and all tabs, but no MemosRawHTML.
        """
        return self.parsers.scrape_profile_only(animal_id)

    def scrape_full_details(self, animal_id: str, internal_id: str) -> Dict[str, Any]:
        """
        Scrape profile + memos page (full details for tooling/tests).
        Returns dict with profile data and MemosRawHTML.
        """
        return self.parsers.scrape_full_details(animal_id, internal_id)

    def scrape_dog_details(self, animal_id: str, internal_id: str) -> Dict[str, Any]:
        """
        Scrapes all required data for a single dog (backwards compatibility).
        Returns normalized data structure with consistent keys.
        """
        return self.parsers.scrape_dog_details(animal_id, internal_id)


"""
Main ShelterLuv scraper class.

Combines session management with data parsing to provide a complete scraping API.
"""

from typing import Any, Dict

from .navigation import SELECTORS
from .parsers import ShelterLuvParsers
from .session import ShelterLuvSession


class ShelterLuvScraper:
    """
    Complete ShelterLuv scraper combining session management and data parsing.

    Provides a context manager interface for browser lifecycle management
    and exposes parsing methods for data extraction.
    """

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session: ShelterLuvSession = None
        self.parsers: ShelterLuvParsers = None

    def __enter__(self):
        """Initialize browser session and parsers."""
        self.session = ShelterLuvSession(self.username, self.password)
        self.session.__enter__()
        self.parsers = ShelterLuvParsers(self.session.page, SELECTORS)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up browser resources."""
        if self.session:
            self.session.__exit__(exc_type, exc_val, exc_tb)

    def scrape_animal_record_summary(self, animal_id: str, internal_id: str) -> Dict[str, Any]:
        """
        Scrape the animal record summary page.

        Args:
            animal_id: The ShelterLuv animal ID
            internal_id: The internal database ID

        Returns:
            Dict containing scraped animal data
        """
        return self.parsers.scrape_animal_record_summary(animal_id, internal_id)

    def scrape_profile_only(self, animal_id: str) -> Dict[str, Any]:
        """
        Scrape only the animal profile page for basic information.

        Args:
            animal_id: The ShelterLuv animal ID

        Returns:
            Dict containing basic profile data
        """
        return self.parsers.scrape_profile_only(animal_id)

    def scrape_full_details(self, animal_id: str, internal_id: str) -> Dict[str, Any]:
        """
        Scrape comprehensive details for an animal.

        Args:
            animal_id: The ShelterLuv animal ID
            internal_id: The internal database ID

        Returns:
            Dict containing comprehensive animal data
        """
        return self.parsers.scrape_full_details(animal_id, internal_id)

    def scrape_dog_details(self, animal_id: str, internal_id: str) -> Dict[str, Any]:
        """
        Scrape detailed dog information.

        Args:
            animal_id: The ShelterLuv animal ID
            internal_id: The internal database ID

        Returns:
            Dict containing detailed dog data
        """
        return self.parsers.scrape_dog_details(animal_id, internal_id)

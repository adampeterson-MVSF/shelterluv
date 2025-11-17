"""
Tests for scraper package - ShelterLuv web scraping functionality.
Tests the minimal public API: scrape_profile_only and scrape_full_details.

These are INTEGRATION tests that require browser setup and should be run separately
from unit tests. Mark with @pytest.mark.integration
"""

from unittest.mock import Mock, patch

import pytest

from errors import ScraperError
from scraper import ShelterLuvScraper


@pytest.mark.integration
class TestShelterLuvScraper:
    """Test the ShelterLuvScraper minimal public API."""

    def test_scraper_has_minimal_api(self):
        """Test that ShelterLuvScraper has the required minimal API methods."""
        scraper = ShelterLuvScraper("test_user", "test_pass")

        # Check that the required methods exist
        assert hasattr(scraper, "scrape_profile_only")
        assert hasattr(scraper, "scrape_full_details")
        assert callable(getattr(scraper, "scrape_profile_only"))
        assert callable(getattr(scraper, "scrape_full_details"))

    @pytest.mark.skip(reason="Integration test requires browser setup")
    def test_scrape_profile_only_integration(self):
        """Integration test for scrape_profile_only (skipped in CI)."""
        # This would test the actual scraping functionality
        # but requires browser setup, so it's skipped
        pass

    @pytest.mark.skip(reason="Integration test requires browser setup")
    def test_scrape_full_details_integration(self):
        """Integration test for scrape_full_details (skipped in CI)."""
        # This would test the actual scraping functionality
        # but requires browser setup, so it's skipped
        pass

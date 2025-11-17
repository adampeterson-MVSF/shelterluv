"""
Tests for in_custody_ids scraper module.

Tests the logic for extracting Internal IDs from ShelterLuv's in-custody table.
Uses static HTML fixtures to avoid hitting live ShelterLuv during tests.
"""

from unittest.mock import Mock, patch

import pytest
from playwright.sync_api import Browser, BrowserContext, Page

# Static HTML fixture representing a typical ShelterLuv in-custody table
# This is a simplified version with just the table structure and some sample data
IN_CUSTODY_TABLE_HTML = """
<!DOCTYPE html>
<html>
<body>
    <div class="table-responsive">
        <table class="table table-striped">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>ID</th>
                    <th>Internal-ID</th>
                    <th>Status</th>
                    <th>Age</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><a href="/animals/12345">Buddy</a></td>
                    <td>A001</td>
                    <td>27305831</td>
                    <td>Available</td>
                    <td>2 years</td>
                </tr>
                <tr>
                    <td><a href="/animals/12346">Max</a></td>
                    <td>A002</td>
                    <td>27305832</td>
                    <td>Pending</td>
                    <td>1 year</td>
                </tr>
                <tr>
                    <td><a href="/animals/12347">Bella</a></td>
                    <td>A003</td>
                    <td>27305833</td>
                    <td>Available</td>
                    <td>3 years</td>
                </tr>
                <tr>
                    <td><a href="/animals/12348">Charlie</a></td>
                    <td>A004</td>
                    <td>27305834</td>
                    <td>Hold</td>
                    <td>5 years</td>
                </tr>
                <tr>
                    <td><a href="/animals/12349">Luna</a></td>
                    <td>A005</td>
                    <td>invalid-id</td>
                    <td>Available</td>
                    <td>4 years</td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- Pagination controls -->
    <nav aria-label="Table pagination">
        <ul class="pagination">
            <li class="page-item disabled">
                <a class="page-link" href="#" tabindex="-1">Previous</a>
            </li>
            <li class="page-item active">
                <a class="page-link" href="#">1</a>
            </li>
            <li class="page-item">
                <a class="page-link" href="#">2</a>
            </li>
            <li class="page-item">
                <a class="page-link" href="#">Next</a>
            </li>
        </ul>
    </nav>
</body>
</html>
"""


class TestInCustodyIdsScraper:
    """Test suite for in_custody_ids scraper functions."""

    @patch("scraper.in_custody_ids.ShelterLuvSession")
    def test_scrape_in_custody_ids_integration(self, mock_session_class):
        """Integration test for scrape_in_custody_ids function."""
        from scraper.in_custody_ids import scrape_in_custody_ids

        # Mock session
        mock_session = Mock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session_class.return_value.__exit__.return_value = None

        # Mock page
        mock_page = Mock()
        mock_session.page = mock_page

        # Mock navigation to dashboard
        mock_page.goto = Mock()
        mock_page.wait_for_load_state = Mock()
        mock_page.wait_for_timeout = Mock()

        # Mock "In Custody View" button not being found (may already be active)
        mock_page.get_by_text = Mock()
        mock_page.get_by_text.return_value.count.return_value = 0

        # Mock data-cy animal rows - simulate 0 found (broken selectors)
        mock_animal_rows = Mock()
        mock_animal_rows.count.return_value = 0
        mock_page.locator.return_value = mock_animal_rows

        # Call function
        result = scrape_in_custody_ids("user", "pass")

        # Verify session was created
        mock_session_class.assert_called_once_with("user", "pass")

        # Verify navigation was called
        mock_page.goto.assert_called_once_with(
            "https://new.shelterluv.com/dashboard?tab=animals",
            wait_until="domcontentloaded",
            timeout=30000,
        )

        # Should return empty set since no animal rows found
        assert result == set()

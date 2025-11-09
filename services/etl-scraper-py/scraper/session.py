"""
Session management for ShelterLuv scraper.

Handles browser lifecycle, login, and session state.
"""

from playwright.sync_api import sync_playwright, Page, Browser
from typing import Optional
import re
from errors import ScraperError

# Login-related selectors
SELECTORS = {
    "login_username": 'input[name="username"]',
    "login_password": 'input[name="password"]',
    "login_submit": 'button[type="submit"]',
    # Accessible-name fallbacks used if the above fail
    "login_username_label_re": re.compile(r"user(name)?|email", re.I),
    "login_password_label_re": re.compile(r"pass(word)?", re.I),
    "login_submit_role_re": re.compile(r"log ?in|sign ?in", re.I),
    # Post-login readiness
    "post_login_url_pattern": "https://new.shelterluv.com/**",
}


class ShelterLuvSession:
    """
    Browser session management for ShelterLuv data extraction.
    """

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context = None
        self.page: Optional[Page] = None

    def _find_input_by_label_regex(self, regex: re.Pattern, timeout_ms: int = 5000) -> str:
        """Find input element by label regex and return its value."""
        assert self.page is not None
        locator = self.page.get_by_label(regex).first
        return locator.input_value(timeout=timeout_ms).strip()

    def _fill_input_by_label_regex(self, regex: re.Pattern, value: str, timeout_ms: int = 5000) -> None:
        """Find input element by label regex and fill it with value."""
        assert self.page is not None
        locator = self.page.get_by_label(regex).first
        locator.fill(value, timeout=timeout_ms)

    def _click_button_by_text_regex(self, regex: re.Pattern, timeout_ms: int = 5000) -> None:
        """Find and click button by text regex."""
        assert self.page is not None
        locator = self.page.get_by_role("button", name=regex).first
        locator.click(timeout=timeout_ms)

    def __enter__(self):
        """Initialize browser and login."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context(
            user_agent="Muttville-Internal-Scraper-Bot"
        )
        self.page = self.context.new_page()
        self._login()
        assert self.page is not None  # Type assertion for mypy
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up browser resources."""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def _login(self):
        """Log into ShelterLuv with robust fallbacks."""
        try:
            self.page.goto("https://new.shelterluv.com/login")

            # Try primary CSS inputs first
            try:
                self.page.locator(SELECTORS["login_username"]).first.fill(self.username, timeout=3000)
                self.page.locator(SELECTORS["login_password"]).first.fill(self.password, timeout=3000)
            except Exception:
                # Fallback to accessible-name labels if CSS not found
                self._fill_input_by_label_regex(SELECTORS["login_username_label_re"], self.username, timeout_ms=4000)
                self._fill_input_by_label_regex(SELECTORS["login_password_label_re"], self.password, timeout_ms=4000)

            # Click submit via role first, else CSS
            try:
                self._click_button_by_text_regex(SELECTORS["login_submit_role_re"], timeout_ms=4000)
            except Exception:
                self.page.locator(SELECTORS["login_submit"]).first.click(timeout=4000)

            # Be resilient to deep-links or dashboards
            try:
                self.page.wait_for_url(SELECTORS["post_login_url_pattern"], timeout=15000)
            except Exception:
                # As a secondary signal, check if we're no longer on login page and on shelterluv domain
                self.page.wait_for_timeout(2000)  # Brief wait for page to settle
                if "login" in self.page.url.lower():
                    raise ScraperError("Still on login page after login attempt")
                # Check if we're on the expected shelterluv domain
                if "new.shelterluv.com" not in self.page.url:
                    raise ScraperError(f"Login failed: not on expected ShelterLuv domain. Current URL: {self.page.url}")
                # If we get here, login was successful
        except Exception as e:
            raise ScraperError(f"Login failed: {e}")

    def goto_in_custody_view(self):
        """
        Navigate to the In Custody view from dashboard.
        Assumes login has already been completed.
        """
        assert self.page is not None

        try:
            # Start from dashboard (already logged in)
            self.page.goto("https://new.shelterluv.com/dashboard")
            self.page.wait_for_load_state('networkidle')

            # Debug: Log all visible text elements to understand current UI
            print("DEBUG: Looking for navigation elements...")
            try:
                # Get all visible links and buttons
                all_links = self.page.locator('a, button, [role="button"], [role="tab"]').all_text_contents()
                print(f"DEBUG: Found {len(all_links)} clickable elements:")
                for i, text in enumerate(all_links[:20]):  # Show first 20
                    print(f"  {i+1}: '{text}'")
                if len(all_links) > 20:
                    print(f"  ... and {len(all_links) - 20} more")
            except Exception as e:
                print(f"DEBUG: Could not enumerate clickable elements: {e}")

            # Navigate to Animals section
            # Try multiple approaches for "Animals" menu
            animals_found = False
            for selector in [
                'a:has-text("Animals")',
                'button:has-text("Animals")',
                '[role="button"]:has-text("Animals")',
                'a:has-text("Intake")',
                'button:has-text("Intake")',
                '[role="button"]:has-text("Intake")',
                'nav a',  # Any nav links
                '.nav a',
                '.sidebar a'
            ]:
                try:
                    locator = self.page.locator(selector).first
                    if locator.is_visible(timeout=1000):
                        text = locator.text_content().strip()
                        print(f"DEBUG: Trying to click '{text}' with selector '{selector}'")
                        locator.click(timeout=2000)
                        animals_found = True
                        break
                except Exception as e:
                    print(f"DEBUG: Selector '{selector}' failed: {e}")
                    continue

            if not animals_found:
                raise ScraperError("Could not find Animals/Intake menu item - check UI structure")

            # Wait a bit for navigation
            self.page.wait_for_timeout(1000)

            # Click "In Custody View" tab
            custody_found = False
            for selector in [
                'a:has-text("In Custody View")',
                'button:has-text("In Custody View")',
                '[role="tab"]:has-text("In Custody View")',
                'a:has-text("In Custody")',
                'button:has-text("In Custody")',
                '[role="tab"]:has-text("In Custody")'
            ]:
                try:
                    locator = self.page.locator(selector).first
                    if locator.is_visible(timeout=1000):
                        text = locator.text_content().strip()
                        print(f"DEBUG: Trying to click '{text}' with selector '{selector}'")
                        locator.click(timeout=2000)
                        custody_found = True
                        break
                except Exception as e:
                    print(f"DEBUG: Selector '{selector}' failed: {e}")
                    continue

            if not custody_found:
                # Try getting all tab-like elements and show them
                try:
                    tabs = self.page.locator('[role="tab"], .tab, .nav-tabs a').all_text_contents()
                    print(f"DEBUG: Available tabs: {tabs}")
                except Exception as e:
                    print(f"DEBUG: Could not enumerate tabs: {e}")
                raise ScraperError("Could not find In Custody View tab - check UI structure")

            # Wait a bit for content to load
            self.page.wait_for_timeout(2000)

            # Check what content is actually loaded
            print(f"DEBUG: Current URL: {self.page.url}")
            try:
                page_title = self.page.locator('h1, .page-title, title').first.text_content(timeout=2000)
                print(f"DEBUG: Page title/content: '{page_title}'")
            except Exception as e:
                print(f"DEBUG: Could not get page title: {e}")

            # Try direct navigation to in-custody URL if current approach fails
            current_url = self.page.url
            if 'tab=animals' in current_url and 'section=' in current_url:
                print("DEBUG: Trying direct navigation to in-custody section")
                try:
                    # Try setting the section parameter
                    self.page.goto("https://new.shelterluv.com/dashboard?tab=animals&section=in_custody")
                    self.page.wait_for_timeout(2000)
                    print(f"DEBUG: After direct navigation: {self.page.url}")
                except Exception as e:
                    print(f"DEBUG: Direct navigation failed: {e}")

            # The In Custody view appears to load content dynamically via JavaScript
            # Wait for dynamic content to load
            print("DEBUG: Waiting for dynamic table content to load...")
            self.page.wait_for_timeout(5000)  # Give more time for JS to execute

            # Check for table content with multiple attempts and selectors
            table_found = False
            for attempt in range(3):
                print(f"DEBUG: Attempt {attempt + 1} to find table content...")

                for selector in [
                    "tbody tr",
                    "table tr",
                    ".table tr",
                    ".data-table tr",
                    "[role='table'] [role='row']",
                    ".table-responsive tbody tr",
                    ".animals-table tbody tr"
                ]:
                    try:
                        rows = self.page.locator(selector)
                        count = rows.count()
                        if count > 0:
                            print(f"DEBUG: Found {count} table rows with selector: {selector}")
                            table_found = True
                            break
                    except Exception:
                        continue

                if table_found:
                    break

                # Wait a bit more between attempts
                self.page.wait_for_timeout(2000)

            if not table_found:
                # Try to see if there are any network requests that might give us clues
                print("DEBUG: No table found. Checking for alternative data sources...")

                # Check if there are any JSON data attributes or hidden inputs
                try:
                    scripts = self.page.locator('script[type="application/json"], script:not([src])').all_text_contents()
                    for script in scripts:
                        if 'Internal-ID' in script or 'animals' in script.lower():
                            print(f"DEBUG: Found potential JSON data: {script[:200]}...")
                            break
                except Exception as e:
                    print(f"DEBUG: Could not check scripts: {e}")

                # Check for any API endpoints in network requests (this would require more complex setup)
                print("DEBUG: Consider checking Network tab for JSON endpoints that load table data")

                # For now, fall back to API-based approach
                raise ScraperError("Could not find table elements. The In Custody view may load data via API endpoints rather than direct HTML. Consider using the Network tab to find the JSON endpoint that populates this table.")

        except Exception as e:
            raise ScraperError(f"Failed to navigate to In Custody view: {e}")

    def close(self):
        """Legacy close method for backward compatibility."""
        self.__exit__(None, None, None)

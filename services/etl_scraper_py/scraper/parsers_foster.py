"""
Foster information parsing functions for ShelterLuv scraper.

Handles extraction of foster person information from animal profile pages,
including name and profile links.
"""

from typing import Any, Dict, Optional
import re


def scrape_foster_info(page) -> Dict[str, Any]:
    """
    Scrape foster person information from animal profile page.

    Looks for patterns like:
    - "Foster: [Name]" with optional link to person profile
    - Extracts name and person ID from profile URL

    Returns:
        Dict with foster information or empty dict if no foster found
    """
    result = {}

    try:
        # Wait for the page to be fully loaded and dynamic content to appear
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)  # Initial wait

        # Debug: Check current URL
        current_url = page.url
        print(f"DEBUG: Scraping foster info from URL: {current_url}")

        # Wait for Livewire components to load by waiting for wire:id elements
        try:
            page.locator('[wire\\:id]').first.wait_for(timeout=10000)
            print("DEBUG: Livewire components loaded")
        except Exception as e:
            print(f"DEBUG: No Livewire components found or timeout: {e}")

        # Specifically wait for the location/foster component (from user's HTML)
        try:
            # The user's HTML shows wire:id="HFXFTuAppYRIVS4biMb1" for the foster component
            foster_component = page.locator('[wire\\:id="HFXFTuAppYRIVS4biMb1"]').first
            foster_component.wait_for(timeout=5000)
            print("DEBUG: Foster component loaded")
        except Exception as e:
            print(f"DEBUG: Foster component not found or didn't load: {e}")

        # Debug: Check for any wire:id elements on the page
        try:
            wire_elements = page.locator('[wire\\:id]').all()
            print(f"DEBUG: Found {len(wire_elements)} wire:id elements")
            for i, elem in enumerate(wire_elements[:3]):  # Show first 3
                try:
                    wire_id = elem.get_attribute('wire:id', timeout=1000)
                    inner_text = elem.inner_text(timeout=1000).strip()[:100]  # First 100 chars
                    print(f"DEBUG: wire:id element {i}: {wire_id} - text: '{inner_text}'")
                except Exception as e:
                    print(f"DEBUG: Error getting wire:id element {i}: {e}")
        except Exception as e:
            print(f"DEBUG: Error finding wire:id elements: {e}")

        # Look for foster information in various possible structures
        # The HTML shows it's in a div with specific classes and contains "Foster:" text

        # Try the specific wire:id component that contains foster info (from user's HTML)
        try:
            foster_component = page.locator('[wire\\:id="HFXFTuAppYRIVS4biMb1"]').first
            print(f"DEBUG: Looking for specific wire:id component, count: {foster_component.count()}")
            if foster_component.count() > 0:
                text_content = foster_component.inner_text(timeout=2000).strip()
                print(f"DEBUG: Specific wire:id component text: '{text_content}'")
                if 'Foster:' in text_content:
                    print("DEBUG: Found 'Foster:' in specific wire:id component!")
                    # Found foster info! Look for the link inside
                    foster_link = foster_component.locator('a[href*="person/"]').first
                    print(f"DEBUG: Foster links found in component: {foster_link.count()}")

                    if foster_link.count() > 0:
                        # Get the link href and text
                        href = foster_link.get_attribute('href', timeout=2000)
                        name = foster_link.inner_text(timeout=2000).strip()
                        print(f"DEBUG: Found foster link: {name} -> {href}")

                        if href and name:
                            # Extract person ID from URL like "/person/MVSF-P-7213"
                            person_id_match = re.search(r'/person/([A-Z]+-P-\d+)', href)
                            if person_id_match:
                                person_id = person_id_match.group(1)
                                print(f"DEBUG: Extracted person ID: {person_id}")

                                result['foster_name'] = name
                                result['foster_person_id'] = person_id
                                result['foster_profile_url'] = href
                                result['in_foster'] = True
                                print(f"DEBUG: SUCCESS! Returning foster info: {result}")
                                return result  # Found it, return immediately
        except Exception as e:
            print(f"DEBUG: Error with specific wire:id method: {e}")
            pass  # Continue to other methods

        # Try the exact selector from the user's HTML
        try:
            foster_containers = page.locator('div.flex.items-center.text-body-2.gap-2').all()
            print(f"DEBUG: Found {len(foster_containers)} containers with exact selector")
            for i, container in enumerate(foster_containers):
                text_content = container.inner_text(timeout=2000).strip()
                if 'Foster:' in text_content:
                    print(f"DEBUG: Found 'Foster:' in container {i} text!")
                    # Found foster info! Look for the link inside
                    foster_link = container.locator('a[href*="person/"]').first
                    print(f"DEBUG: Foster links found in container {i}: {foster_link.count()}")

                    if foster_link.count() > 0:
                        # Get the link href and text
                        href = foster_link.get_attribute('href', timeout=2000)
                        name = foster_link.inner_text(timeout=2000).strip()
                        print(f"DEBUG: Found foster link in container {i}: {name} -> {href}")

                        if href and name:
                            # Extract person ID from URL like "/person/MVSF-P-7213"
                            person_id_match = re.search(r'/person/([A-Z]+-P-\d+)', href)
                            if person_id_match:
                                person_id = person_id_match.group(1)
                                print(f"DEBUG: Extracted person ID from container {i}: {person_id}")

                                result['foster_name'] = name
                                result['foster_person_id'] = person_id
                                result['foster_profile_url'] = href
                                result['in_foster'] = True
                                print(f"DEBUG: SUCCESS! Returning foster info from container method: {result}")
                                return result  # Found it, return immediately
        except Exception:
            pass  # Continue to other methods

        # Try multiple selectors that might contain foster info
        foster_selectors = [
            '[wire\\:id]',  # Any Livewire component
            'div[wire\\:snapshot]',  # Livewire snapshot containers
            'p:has-text("Foster:")',  # Direct paragraph with Foster text
        ]

        for selector in foster_selectors:
            try:
                containers = page.locator(selector).all()

                for container in containers:
                    # Check if this container contains "Foster:"
                    text_content = container.inner_text(timeout=2000).strip()
                    if 'Foster:' in text_content:
                        # Found foster info! Look for the link inside
                        foster_link = container.locator('a[href*="person/"]').first

                        if foster_link.count() > 0:
                            # Get the link href and text
                            href = foster_link.get_attribute('href', timeout=2000)
                            name = foster_link.inner_text(timeout=2000).strip()

                            if href and name:
                                # Extract person ID from URL like "/person/MVSF-P-7213"
                                person_id_match = re.search(r'/person/([A-Z]+-P-\d+)', href)
                                if person_id_match:
                                    person_id = person_id_match.group(1)

                                    result['foster_name'] = name
                                    result['foster_person_id'] = person_id
                                    # href already includes the full URL, don't prepend it
                                    result['foster_profile_url'] = href
                                    result['in_foster'] = True
                                    print(f"Found foster info with fallback selector: {name} (ID: {person_id})")
                                    return result  # Found it, return immediately

            except Exception:
                continue

        # Fallback: try the old method if specific structure didn't work
        foster_elements = page.locator('text=/Foster:/i').all()

        for element in foster_elements:
            try:
                # Get the parent element that contains the foster info
                parent = element.locator('xpath=ancestor-or-self::*[contains(text(), "Foster:")]').first

                if parent.count() > 0:
                    text = parent.inner_text(timeout=2000).strip()

                    # Extract name after "Foster:"
                    match = re.search(r'Foster:\s*(.+?)(?:\s|$)', text, re.IGNORECASE)
                    if match:
                        foster_name = match.group(1).strip()

                        # Clean up common trailing text
                        foster_name = re.sub(r'\s*\([^)]*\)\s*$', '', foster_name)  # Remove parentheses
                        foster_name = foster_name.strip()

                        result['foster_name'] = foster_name
                        result['in_foster'] = True

                        # Look for a link in or near this element
                        link = parent.locator('a').first
                        if link.count() > 0:
                            href = link.get_attribute('href', timeout=1000)
                            if href:
                                # Extract person ID from URL like /person/MVSF-P-7213
                                person_match = re.search(r'/person/([A-Z0-9-]+)', href)
                                if person_match:
                                    result['foster_person_id'] = person_match.group(1)
                                    result['foster_profile_url'] = href

                        # Found foster info, return
                        return result

            except Exception:
                continue

        # Alternative approach: look for specific foster-related selectors
        if not result:
            # Try common foster display patterns
            foster_selectors = [
                '[class*="foster" i]',
                '[data-foster]',
                '.foster-info',
                '[title*="foster" i]'
            ]

            for selector in foster_selectors:
                try:
                    elements = page.locator(selector).all()
                    for element in elements:
                        text = element.inner_text(timeout=1000).strip()
                        if 'foster' in text.lower() and ':' in text:
                            # Extract name after colon
                            parts = text.split(':', 1)
                            if len(parts) > 1:
                                foster_name = parts[1].strip()
                                if foster_name:
                                    result['foster_name'] = foster_name

                                    # Look for links
                                    link = element.locator('a').first
                                    if link.count() > 0:
                                        href = link.get_attribute('href', timeout=1000)
                                        if href and '/person/' in href:
                                            person_match = re.search(r'/person/([A-Z0-9-]+)', href)
                                            if person_match:
                                                result['foster_person_id'] = person_match.group(1)
                                                result['foster_profile_url'] = href

                                    break
                    if result:
                        break
                except Exception:
                    continue

    except Exception as e:
        # Log but don't fail - foster info is optional
        print(f"Warning: Could not scrape foster info: {e}")

    return result


def scrape_person_profile(page, person_id: str) -> Dict[str, Any]:
    """
    Scrape additional information from a person profile page.

    Args:
        page: Playwright page object
        person_id: Person ID (e.g., 'MVSF-P-7213')

    Returns:
        Dict with additional person information
    """
    result = {}

    try:
        # Basic info fields to extract
        field_mappings = {
            "Phone": "phone",
            "Email": "email",
            "Address": "address",
            "Emergency Contact": "emergency_contact",
            "Relationship": "relationship_type",
        }

        for label, field_name in field_mappings.items():
            try:
                # Look for fieldsets with specific labels
                xpath_selector = f'//fieldset[label[normalize-space()="{label}"]]//button | //fieldset[label[normalize-space()="{label}"]]//input | //fieldset[label[normalize-space()="{label}"]]//span'

                elements = page.locator(f"xpath={xpath_selector}")
                if elements.count() > 0:
                    # Get text from first matching element
                    if elements.first.locator("input").count() > 0:
                        value = elements.first.locator("input").get_attribute("value", timeout=1000)
                    else:
                        value = elements.first.inner_text(timeout=1000).strip()

                    if value:
                        result[field_name] = value

            except Exception:
                continue

        # Look for additional contact information in other sections
        try:
            # Try to find contact info in main content areas
            contact_selectors = [
                '[class*="contact" i]',
                '[class*="phone" i]',
                '[class*="email" i]',
                '.person-details',
                '.profile-info'
            ]

            for selector in contact_selectors:
                try:
                    elements = page.locator(selector).all()
                    for element in elements:
                        text = element.inner_text(timeout=1000).strip()
                        if text and len(text) > 5:  # Skip very short text
                            # Look for phone patterns
                            phone_match = re.search(r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', text)
                            if phone_match and 'phone' not in result:
                                result['phone'] = phone_match.group(1)

                            # Look for email patterns
                            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
                            if email_match and 'email' not in result:
                                result['email'] = email_match.group(1)
                except Exception:
                    continue

        except Exception:
            pass

    except Exception as e:
        print(f"Warning: Could not scrape person profile for {person_id}: {e}")

    return result

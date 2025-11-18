#!/usr/bin/env python3
"""
Troubleshooting script for foster information scraping.

This script analyzes the foster scraping issue without requiring actual ShelterLuv access.
It examines the HTML structure and provides recommendations for fixing the scraper.
"""

import re
from typing import Dict, Any


def analyze_foster_html(html_content: str) -> Dict[str, Any]:
    """
    Analyze HTML content for foster information patterns.

    Args:
        html_content: Raw HTML from a ShelterLuv animal profile page

    Returns:
        Dict with analysis results
    """
    results = {
        "foster_info_found": False,
        "foster_name": None,
        "foster_person_id": None,
        "foster_profile_url": None,
        "wire_components": [],
        "foster_selectors_found": [],
        "recommendations": []
    }

    # Look for the specific wire:id from the user's HTML
    wire_id_pattern = r'wire:id="([^"]*HFXFTuAppYRIVS4biMb1[^"]*)"'
    wire_matches = re.findall(wire_id_pattern, html_content, re.IGNORECASE)
    if wire_matches:
        results["wire_components"].extend(wire_matches)
        results["recommendations"].append("Found foster component wire:id - scraper should wait for this element")

    # Look for the exact selector from user's HTML
    if 'div.flex.items-center.text-body-2.gap-2' in html_content:
        results["foster_selectors_found"].append("div.flex.items-center.text-body-2.gap-2")

    # Look for Foster: text pattern
    foster_text_pattern = r'Foster:\s*([^<\n]+?)(?:\s*<|\s*$)'
    foster_matches = re.findall(foster_text_pattern, html_content, re.IGNORECASE)
    if foster_matches:
        results["foster_name"] = foster_matches[0].strip()
        results["foster_info_found"] = True
        results["recommendations"].append("Found 'Foster:' text pattern in HTML")

    # Look for person profile links
    person_link_pattern = r'href="([^"]*?/person/[^"]*?)"[^>]*>([^<]*Wendy Hamilton[^<]*)</a>'
    person_matches = re.findall(person_link_pattern, html_content, re.IGNORECASE)
    if person_matches:
        url, name = person_matches[0]
        results["foster_profile_url"] = url
        results["foster_name"] = name.strip()

        # Extract person ID
        person_id_match = re.search(r'/person/([A-Z]+-P-\d+)', url)
        if person_id_match:
            results["foster_person_id"] = person_id_match.group(1)
            results["recommendations"].append("Found person profile link with ID")

    # Check for Livewire components
    if 'wire:snapshot' in html_content:
        results["recommendations"].append("Page uses Livewire - scraper needs to wait for dynamic content")

    if 'wire:effects' in html_content:
        results["recommendations"].append("Page has wire:effects - content loads asynchronously")

    # Check for potential timing issues
    if results["foster_info_found"] and not results["wire_components"]:
        results["recommendations"].append("Foster info exists but no wire:id found - may load after initial page load")

    return results


def main():
    """Main function to run the troubleshooting analysis."""

    # This is the HTML content the user provided (simplified)
    html_content = '''<div wire:snapshot="..." wire:effects="..." wire:id="HFXFTuAppYRIVS4biMb1" class="flex items-center text-body-2 gap-2">
    <p>
        Foster: <a href="https://new.shelterluv.com/person/MVSF-P-6990">Wendy Hamilton</a>
    </p>
</div>'''

    print("🔍 Troubleshooting Foster Information Scraping")
    print("=" * 60)
    print(f"Target URL: https://new.shelterluv.com/animal/MVSF-A-56497")
    print(f"Expected foster info: Wendy Hamilton (MVSF-P-6990)")
    print()

    analysis = analyze_foster_html(html_content)

    print("📊 Analysis Results:")
    print(f"   Foster info found: {analysis['foster_info_found']}")
    if analysis['foster_name']:
        print(f"   Foster name: {analysis['foster_name']}")
    if analysis['foster_person_id']:
        print(f"   Person ID: {analysis['foster_person_id']}")
    if analysis['foster_profile_url']:
        print(f"   Profile URL: {analysis['foster_profile_url']}")

    print(f"\n   Wire components found: {len(analysis['wire_components'])}")
    for wire_id in analysis['wire_components']:
        print(f"     - {wire_id}")

    print(f"\n   Selectors found: {len(analysis['foster_selectors_found'])}")
    for selector in analysis['foster_selectors_found']:
        print(f"     - {selector}")

    print("\n💡 Recommendations:")
    for rec in analysis['recommendations']:
        print(f"   • {rec}")

    print("\n🔧 Current Scraper Issues:")
    print("   1. Scraper may not be waiting long enough for Livewire components to load")
    print("   2. The specific wire:id may be different on different pages/dogs")
    print("   3. Foster info loads asynchronously after initial page render")

    print("\n✅ Suggested Fixes:")
    print("   1. Increase wait time for Livewire components (currently 5-10 seconds)")
    print("   2. Try multiple wire:id patterns, not just the specific one")
    print("   3. Wait for networkidle AND specific element visibility")
    print("   4. Add retry logic for dynamic content loading")

    print("\n🧪 Test Commands:")
    print("   # Test with current dog")
    print("   cd services/etl_scraper_py && python3 run_etl_local.py --limit 1")
    print("   ")
    print("   # Check if foster info appears in scraped data")
    print("   # Look for 'Dogs with foster info' in output")


if __name__ == "__main__":
    main()

"""
ShelterLuv API client for event-related operations.
"""

from typing import List, Dict, Any
from .api_client_base import _make_api_request, BASE_URL

# Event/people caps: Allow more events than animals since each animal can have multiple events
MAX_EVENTS_PER_ANIMAL = 5

def _filter_relevant_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter events to only include relevant ones for ETL processing."""
    relevant_types = {
        "Intake",
        "Adoption",
        "Transfer",
        "Foster Care",
        "Medical",
        "Behavior",
        "Return",
        "Foster",      # Used by foster_mapping.py
        "FosterReturn", # Used by foster_mapping.py
        "Event"        # Used for event participation tracking
    }

    return [
        event for event in events
        if event.get("Type", "") in relevant_types
    ]

def get_animal_events(api_key: str) -> List[Dict[str, Any]]:
    """
    Fetch all animal events from ShelterLuv API.

    Args:
        api_key: ShelterLuv API key

    Returns:
        List of event dictionaries
    """
    headers = {"X-API-Key": api_key}

    # Get all events (paginated)
    all_events = []
    page = 1

    while True:
        params = {
            "page": page,
            "per_page": 100,  # API max is 100 per page
            "include": "Internal-ID,Type,Subtype,DateTime,Notes,Person"
        }

        data = _make_api_request(f"{BASE_URL}/events", headers, params)

        if not data.get("events"):
            break

        events = data["events"]
        filtered_events = _filter_relevant_events(events)
        all_events.extend(filtered_events)

        # Check if there are more pages
        if len(events) < 100:
            break

        page += 1

    # Sort events chronologically (oldest first) for consistent processing
    all_events.sort(key=lambda e: e.get('Date', ''))

    return all_events

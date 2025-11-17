"""
ShelterLuv API client for event-related operations.
"""

from typing import Any, Dict, List

from .api_client_base import BASE_URL, _make_api_request


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
        "Foster",  # Used by foster_mapping.py
        "FosterReturn",  # Used by foster_mapping.py
        "Event",  # Used for event participation tracking
    }

    return [event for event in events if event.get("Type", "") in relevant_types]


def get_animal_events(api_key: str) -> List[Dict[str, Any]]:
    """
    Fetch all animal events from ShelterLuv API.

    Args:
        api_key: ShelterLuv API key

    Returns:
        List of event dictionaries
    """
    import logging

    logger = logging.getLogger(__name__)
    headers = {"X-API-Key": api_key}

    # Get all events (paginated)
    all_events: List[Dict[str, Any]] = []
    page = 1
    MAX_PAGES = 100  # Safety limit to prevent infinite loops
    pages_without_relevant_events = 0  # Track consecutive pages with no relevant events

    while page <= MAX_PAGES:
        params = {
            "page": page,
            "per_page": 100,  # API max is 100 per page
            "include": "Internal-ID,Type,Subtype,DateTime,Notes,Person",
        }

        try:
            data = _make_api_request(f"{BASE_URL}/events", headers, params)
        except Exception as e:
            # If we've already fetched some events, log warning and return what we have
            if all_events:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Events API error on page {page}, returning {len(all_events)} events already fetched: {e}"
                )
                break
            # If no events fetched yet, re-raise the error
            raise

        if not data.get("events"):
            break

        events = data["events"]
        filtered_events = _filter_relevant_events(events)
        all_events.extend(filtered_events)

        # Log what we found on this page
        if events:
            event_types = set(event.get("Type", "") for event in events)
            logger.debug(
                f"Page {page}: {len(events)} events, {len(filtered_events)} relevant. Types: {sorted(event_types)}"
            )
        else:
            logger.debug(f"Page {page}: No events returned")

        # Track consecutive pages without relevant events
        if filtered_events:
            pages_without_relevant_events = 0
        else:
            pages_without_relevant_events += 1

        # Stop if we've had too many consecutive pages without relevant events
        if pages_without_relevant_events >= 5:
            logger.info(
                f"Stopping pagination after {pages_without_relevant_events} consecutive pages without relevant events"
            )
            break

        # Check if there are more pages
        if len(events) < 100:
            break

        page += 1

    if page > MAX_PAGES:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(
            f"Events API pagination hit MAX_PAGES limit ({MAX_PAGES}), stopping pagination"
        )

    # Sort events chronologically (oldest first) for consistent processing
    all_events.sort(key=lambda e: e.get("Date", ""))

    return all_events

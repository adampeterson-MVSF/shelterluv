"""
ShelterLuv API client for people-related operations.
"""

from typing import Any, Dict, List

from .api_client_base import BASE_URL, _make_api_request


def get_people(api_key: str) -> List[Dict[str, Any]]:
    """
    Fetch all people (fosters, adopters, staff) from ShelterLuv API.

    Args:
        api_key: ShelterLuv API key

    Returns:
        List of person dictionaries
    """
    import logging

    logger = logging.getLogger(__name__)
    headers = {"X-API-Key": api_key}

    # Get all people (paginated)
    all_people: List[Dict[str, Any]] = []
    page = 1
    MAX_PAGES = 100  # Safety limit to prevent infinite loops
    pages_without_people = 0  # Track consecutive pages with no people
    REASONABLE_MAX_PAGES = 20  # Stop after this many pages even if we get people

    while page <= MAX_PAGES:
        params = {
            "page": page,
            "per_page": 100,  # API max is 100 per page
            "include": "ID,FirstName,LastName,Email,Phone,Type,Status",
        }

        try:
            data = _make_api_request(f"{BASE_URL}/people", headers, params)
        except Exception as e:
            # If we've already fetched some people, log warning and return what we have
            if all_people:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"People API error on page {page}, returning {len(all_people)} people already fetched: {e}"
                )
                break
            # If no people fetched yet, re-raise the error
            raise

        if not data.get("people"):
            break

        people = data["people"]
        all_people.extend(people)

        # Track consecutive pages without people
        if people:
            pages_without_people = 0
        else:
            pages_without_people += 1

        # Stop if we've had too many consecutive pages without people
        if pages_without_people >= 5:
            logger.info(
                f"Stopping pagination after {pages_without_people} consecutive pages without people"
            )
            break

        # Stop if we've reached a reasonable limit
        if page >= REASONABLE_MAX_PAGES:
            logger.info(
                f"Stopping pagination after reaching reasonable limit of {REASONABLE_MAX_PAGES} pages"
            )
            break

        # Check if there are more pages
        if len(people) < 100:
            break

        page += 1

    if page > MAX_PAGES:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(
            f"People API pagination hit MAX_PAGES limit ({MAX_PAGES}), stopping pagination"
        )

    return all_people

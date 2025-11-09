"""
ShelterLuv API client for people-related operations.
"""

from typing import List, Dict, Any
from .api_client_base import _make_api_request, BASE_URL

# Allow 2x people than animals since fosters can care for multiple dogs
MAX_PEOPLE_PER_ANIMAL = 2

def get_people(api_key: str) -> List[Dict[str, Any]]:
    """
    Fetch all people (fosters, adopters, staff) from ShelterLuv API.

    Args:
        api_key: ShelterLuv API key

    Returns:
        List of person dictionaries
    """
    headers = {"X-API-Key": api_key}

    # Get all people (paginated)
    all_people = []
    page = 1

    while True:
        params = {
            "page": page,
            "per_page": 100,  # API max is 100 per page
            "include": "ID,FirstName,LastName,Email,Phone,Type,Status"
        }

        data = _make_api_request(f"{BASE_URL}/people", headers, params)

        if not data.get("people"):
            break

        people = data["people"]
        all_people.extend(people)

        # Check if there are more pages
        if len(people) < 100:
            break

        page += 1

    return all_people

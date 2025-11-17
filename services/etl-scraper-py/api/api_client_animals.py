"""
ShelterLuv API client for animal-related operations.
"""

from typing import List, Dict, Any, Collection
from concurrent.futures import ThreadPoolExecutor, as_completed
from .api_client_base import _make_api_request, BASE_URL, _validate_animal_records
from errors import ApiError

def _filter_animals_in_custody(animals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter animals to only include those that might be in custody."""
    excluded_statuses = {"Transferred Out", "Serviced Out", "ADOPTED", "Deceased"}
    return [
        animal for animal in animals
        if animal.get("Status", "") not in excluded_statuses
    ]

def get_all_animals_in_custody(api_key: str, max_animals: int = 1000) -> List[Dict[str, Any]]:
    """
    Fetches all animals that might be in custody from the ShelterLuv API.
    Applies minimal API-level filtering to include animals for scraping.

    Args:
        api_key: ShelterLuv API key
        max_animals: Maximum number of animals to fetch

    Returns:
        List of animal dictionaries with basic info
    """
    headers = {"X-API-Key": api_key}

    # Get all animals (paginated)
    all_animals = []
    page = 1

    while True:
        params = {
            "page": page,
            "per_page": 100,  # API max is 100 per page
            "include": "Internal-ID,Name,Status,ID,IntakeDate,Location,Stage,Breed,Gender,Size"
        }

        data = _make_api_request(f"{BASE_URL}/animals", headers, params)

        if not data.get("animals"):
            break

        animals = data["animals"]
        all_animals.extend(animals)

        # Safety cap to prevent infinite loops
        if len(all_animals) >= max_animals:
            raise ApiError(f"Hit {max_animals}-animal cap")

        # Check if there are more pages
        if len(animals) < 100:
            break

        page += 1

    # Filter to likely in-custody animals
    in_custody_animals = _filter_animals_in_custody(all_animals)

    # Validate records have required fields
    _validate_animal_records(in_custody_animals)

    return in_custody_animals

def get_animal_by_internal_id(internal_id: str, api_key: str) -> Dict[str, Any]:
    """
    Fetch a single animal by internal ID.

    Args:
        internal_id: ShelterLuv internal ID
        api_key: ShelterLuv API key

    Returns:
        Animal data dictionary
    """
    headers = {"X-API-Key": api_key}

    data = _make_api_request(f"{BASE_URL}/animals/{internal_id}", headers)

    if not data.get("animal"):
        raise ApiError(f"Animal not found: {internal_id}")

    return data["animal"]

def get_animals_by_ids(internal_ids: Collection[str], api_key: str, max_workers: int = 5) -> Dict[str, Dict[str, Any]]:
    """
    Fetch multiple animals by internal IDs concurrently.

    Args:
        internal_ids: Collection of ShelterLuv internal IDs
        api_key: ShelterLuv API key
        max_workers: Maximum concurrent requests

    Returns:
        Dict mapping internal_id -> animal data
    """
    if not internal_ids:
        return {}

    headers = {"X-API-Key": api_key}
    results = {}

    def fetch_animal(internal_id: str) -> tuple[str, Dict[str, Any]]:
        try:
            data = _make_api_request(f"{BASE_URL}/animals/{internal_id}", headers)
            # API returns animal data directly (not wrapped in {"animal": {...}})
            # Check if response has animal fields (like "Internal-ID" or "ID")
            animal = data if data.get("Internal-ID") or data.get("ID") else data.get("animal", {})
            # Add SourceUpdatedAt timestamp (RFC 3339 UTC with Z) for incremental processing
            # Use current timestamp since API doesn't provide an "Updated" field
            from datetime import datetime, UTC
            if animal and (animal.get("Internal-ID") or animal.get("ID")):
                animal["SourceUpdatedAt"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
                return internal_id, animal
            # If no animal in response, log warning with response structure for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"No animal data in API response for {internal_id}, response keys: {list(data.keys())}")
            return internal_id, {}
        except ApiError as e:
            # Log the error but continue with other animals
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"API error fetching animal {internal_id}: {e}")
            return internal_id, {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch_animal, internal_id) for internal_id in internal_ids]

        for future in as_completed(futures):
            internal_id, animal = future.result()
            if animal:
                results[internal_id] = animal

    return results

def find_shelterluv_ids_by_muttville_ids(muttville_ids: Collection[str], api_key: str, max_pages: int = 10) -> Dict[str, str]:
    """
    Find ShelterLuv internal IDs by Muttville public IDs.
    Useful for cross-referencing between systems.

    Args:
        muttville_ids: Collection of Muttville public IDs
        api_key: ShelterLuv API key
        max_pages: Maximum pages to search

    Returns:
        Dict mapping muttville_id -> shelterluv_internal_id
    """
    if not muttville_ids:
        return {}

    headers = {"X-API-Key": api_key}
    found_ids = {}

    # Convert to set for faster lookup
    muttville_ids_set = set(muttville_ids)

    for page in range(1, max_pages + 1):
        params = {
            "page": page,
            "per_page": 100,
            "include": "Internal-ID,ID"
        }

        data = _make_api_request(f"{BASE_URL}/animals", headers, params)

        if not data.get("animals"):
            break

        for animal in data["animals"]:
            muttville_id = animal.get("ID")
            internal_id = animal.get("Internal-ID")

            if muttville_id and internal_id and muttville_id in muttville_ids_set:
                found_ids[muttville_id] = internal_id

                # Early exit if we found all requested IDs
                if len(found_ids) >= len(muttville_ids):
                    break

        # No more pages if we got less than 100 results
        if len(data["animals"]) < 100:
            break

    return found_ids

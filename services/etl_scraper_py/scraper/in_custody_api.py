"""
API-based scraper for extracting Internal IDs from ShelterLuv.

This module provides functions to use the official ShelterLuv REST API
to get animals currently in custody.
"""

from typing import Any, Dict, Set

from errors import ScraperError


def scrape_in_custody_ids_via_api(username: str, password: str) -> Set[str]:
    """
    Get Internal IDs of animals currently in custody using the official REST API.

    This function uses the official ShelterLuv API endpoints to get all animals
    and filters for those in custody using API-level logic.

    Args:
        username: ShelterLuv login username (unused - API uses token auth)
        password: ShelterLuv login password (unused - API uses token auth)

    Returns:
        Set of Internal IDs currently in custody

    Raises:
        ScraperError: If API calls fail
    """
    # Import here to avoid circular imports
    from api import get_all_animals_in_custody
    from secret_manager import get_shelterluv_creds

    try:
        creds = get_shelterluv_creds()
        # Use the official API to get all animals in custody
        animals_in_custody = get_all_animals_in_custody(creds["api_key"])
        ids = {str(animal["Internal-ID"]) for animal in animals_in_custody}
        return ids

    except Exception as e:
        raise ScraperError(f"Failed to get in-custody IDs via official API: {e}")


def scrape_in_custody_data_via_api(api_key: str) -> Dict[str, Dict[str, Any]]:
    """
    Get comprehensive data for animals currently in custody using the official REST API.

    This function uses the official ShelterLuv API endpoints to get all in-custody dogs
    and returns a dict mapping Internal IDs to full animal data from /animals/{id}.

    Args:
        api_key: ShelterLuv API key

    Returns:
        Dict mapping Internal IDs to dicts containing full animal data

    Raises:
        ScraperError: If API calls fail
    """
    # Import here to avoid circular imports
    from api import get_all_animals_in_custody, get_animals_by_ids

    try:
        # 1. Get all in-custody dogs (dogs-only after API client changes)
        animals_in_custody = get_all_animals_in_custody(api_key)

        # 2. Collect Internal-IDs
        internal_ids = []
        for animal in animals_in_custody:
            internal_id = str(animal.get("Internal-ID") or animal.get("InternalID"))
            if internal_id:
                internal_ids.append(internal_id)

        # 3. Fetch full detail per dog via /animals/{internal_id}
        animals_by_id = get_animals_by_ids(internal_ids, api_key)

        # 4. Return canonical "animals_by_id" mapping used by the rest of the ETL
        return animals_by_id

    except Exception as e:
        raise ScraperError(f"Failed to get in-custody data via official API: {e}")

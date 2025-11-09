"""
API-based scraper for extracting Internal IDs from ShelterLuv.

This module provides functions to use the official ShelterLuv REST API
to get animals currently in custody.
"""

import logging
from typing import Set
from errors import ScraperError

logger = logging.getLogger(__name__)


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
    from ..secret_manager import get_shelterluv_creds
    from ..api import get_all_animals_in_custody

    try:
        creds = get_shelterluv_creds()
        # Use the official API to get all animals in custody
        animals_in_custody = get_all_animals_in_custody(creds["api_key"])
        ids = {str(animal["Internal-ID"]) for animal in animals_in_custody}
        logger.info(f"Found {len(ids)} animals in custody via official API")
        return ids

    except Exception as e:
        raise ScraperError(f"Failed to get in-custody IDs via official API: {e}")

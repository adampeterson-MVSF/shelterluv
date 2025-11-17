"""
API-based scraper for extracting Internal IDs from ShelterLuv.

This module provides functions to use the official ShelterLuv REST API
to get animals currently in custody.
"""

from typing import Dict, Set

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


def scrape_in_custody_data_via_api(creds: Dict[str, str]) -> Dict[str, Dict[str, str]]:
    """
    Get comprehensive data for animals currently in custody using the official REST API.

    This function uses the official ShelterLuv API endpoints to get all animals
    and returns a dict mapping Internal IDs to basic animal data.

    Args:
        creds: ShelterLuv credentials dict with api_key

    Returns:
        Dict mapping Internal IDs to dicts containing basic animal data

    Raises:
        ScraperError: If API calls fail
    """
    # Import here to avoid circular imports
    from api import get_all_animals_in_custody

    try:
        # Use the official API to get all animals in custody
        # Temporarily increase cap to see how many animals there are
        animals_in_custody = get_all_animals_in_custody(creds["api_key"], max_animals=2000)

        # Convert to dict format expected by extract.py
        animal_data = {}
        for animal in animals_in_custody:
            internal_id = str(animal["Internal-ID"])
            # Convert API field names to the format expected by the scraper
            animal_data[internal_id] = {
                "Internal-ID": internal_id,
                "ID": animal.get("ID", ""),
                "Name": animal.get("Name", ""),
                "Status": animal.get("Status", ""),
                "IntakeDate": animal.get("IntakeDate", ""),
                "Location": animal.get("Location", ""),
                "Stage": animal.get("Stage", ""),
                "Breed": animal.get("Breed", ""),
                "Gender": animal.get("Gender", ""),
                "Size": animal.get("Size", ""),
                "Weight": animal.get("Weight", ""),
                "Age": animal.get("Age", ""),
            }

        return animal_data

    except Exception as e:
        raise ScraperError(f"Failed to get in-custody data via official API: {e}")

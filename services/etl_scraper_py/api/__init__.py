"""
ShelterLuv API client package.

This package provides unified access to all ShelterLuv API endpoints
used by the ETL pipeline.
"""

from .api_client_animals import (
    find_shelterluv_ids_by_muttville_ids,
    get_all_animals_in_custody,
    get_animal_by_internal_id,
    get_animals_by_ids,
)
from .api_client_base import BASE_URL, MAX_RETRIES, REQUEST_TIMEOUT
from .api_client_events import get_animal_events
from .api_client_memos import MemoResult, get_animal_memos, get_animals_memos_batch
from .api_client_people import get_people

__all__ = [
    # Base API configuration
    "BASE_URL",
    "REQUEST_TIMEOUT",
    "MAX_RETRIES",
    # API clients
    "get_animals_by_ids",
    "get_all_animals_in_custody",
    "get_animal_by_internal_id",
    "find_shelterluv_ids_by_muttville_ids",
    "get_animal_events",
    "get_people",
    "get_animal_memos",
    "get_animals_memos_batch",
    "MemoResult",
]

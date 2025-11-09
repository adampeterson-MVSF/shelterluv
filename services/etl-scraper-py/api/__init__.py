"""
ShelterLuv API client package.

This package provides unified access to all ShelterLuv API endpoints
used by the ETL pipeline.
"""

from .api_client_base import (
    BASE_URL,
    REQUEST_TIMEOUT,
    MAX_RETRIES
)
from .api_client_animals import (
    get_animals_by_ids,
    get_all_animals_in_custody,
    get_animal_by_internal_id,
    find_shelterluv_ids_by_muttville_ids
)
from .api_client_events import get_animal_events
from .api_client_people import get_people
from .api_client_memos import get_animal_memos

__all__ = [
    # Base API configuration
    'BASE_URL',
    'REQUEST_TIMEOUT',
    'MAX_RETRIES',

    # API clients
    'get_animals_by_ids',
    'get_all_animals_in_custody',
    'get_animal_by_internal_id',
    'find_shelterluv_ids_by_muttville_ids',
    'get_animal_events',
    'get_people',
    'get_animal_memos'
]

"""
Base API client utilities shared across all ShelterLuv API modules.
"""

import requests
import time
import logging
import os
from typing import Dict, Any, List
from errors import ApiError

logger = logging.getLogger(__name__)

# Base API configuration
BASE_URL = "https://new.shelterluv.com/api/v1"

# Rate limiting and retry configuration
REQUEST_TIMEOUT = (3, 10)  # (connect, read) timeouts in seconds
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # Exponential backoff: 1s, 2s, 4s
RATE_LIMIT_DELAY = 0.1  # Small delay between requests to be respectful

# Configurable delays between successful requests (not just retries)
# These help avoid hitting rate limits when paginating through large datasets
API_REQUEST_DELAYS = {
    "default": 0.5,  # 500ms between requests by default
    "events": 1.0,   # Events API is particularly heavy, use 1s delay
    "people": 0.8,   # People API also heavy, use 800ms delay
    "animals": 0.3,  # Animals API is lighter, use 300ms delay
}

# Environment variable to disable rate limiting delays for testing
DISABLE_API_RATE_LIMITING = os.environ.get("DISABLE_API_RATE_LIMITING", "").lower() in ("true", "1", "yes")

def _make_api_request(url: str, headers: Dict[str, str], params: Dict[str, Any] = None, max_retries: int = MAX_RETRIES, request_delay: float = None) -> Dict[str, Any]:
    """
    Make an API request with retry logic and rate limiting.
    Handles rate limits (429), transient errors, and wraps all exceptions in ApiError.

    Args:
        url: API endpoint URL
        headers: Request headers
        params: Query parameters
        max_retries: Maximum number of retry attempts
        request_delay: Delay before making request (for rate limiting between requests)
    """
    # Determine appropriate delay based on API endpoint
    if request_delay is None:
        if DISABLE_API_RATE_LIMITING:
            request_delay = 0.0  # No delay when rate limiting is disabled
        elif "events" in url:
            request_delay = API_REQUEST_DELAYS["events"]
        elif "people" in url:
            request_delay = API_REQUEST_DELAYS["people"]
        elif "animals" in url:
            request_delay = API_REQUEST_DELAYS["animals"]
        else:
            request_delay = API_REQUEST_DELAYS["default"]

    # Rate limiting delay before making the request (not just between retries)
    if request_delay > 0:
        logger.debug(f"Rate limiting: waiting {request_delay}s before API request to {url}")
        time.sleep(request_delay)

    last_exception = None

    for attempt in range(max_retries):
        try:
            # Additional small delay between retry attempts
            if attempt > 0:
                retry_delay = RATE_LIMIT_DELAY * (RETRY_BACKOFF_FACTOR ** attempt)
                logger.warning(f"API request failed, retrying in {retry_delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)

            response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None

            # Handle rate limiting (429) with exponential backoff
            if status_code == 429:
                backoff_time = RETRY_BACKOFF_FACTOR ** attempt
                logger.warning(f"Rate limited (429) on {url}, backing off for {backoff_time}s")
                time.sleep(backoff_time)
                last_exception = e
                continue

            # Don't retry client errors (4xx) except 429
            if status_code and 400 <= status_code < 500 and status_code != 429:
                raise ApiError(f"ShelterLuv API client error ({status_code}): {e}")

            # Retry server errors (5xx) and other issues
            last_exception = e

        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException) as e:
            last_exception = e

            if attempt < max_retries - 1:
                backoff_time = RETRY_BACKOFF_FACTOR ** attempt
                logger.warning(f"Request failed, retrying in {backoff_time}s: {e}")
                time.sleep(backoff_time)
                continue
            else:
                raise ApiError(f"ShelterLuv API request failed after {max_retries} attempts: {e}")

    # If we get here, all retries failed
    raise ApiError(f"ShelterLuv API request failed after {max_retries} attempts. Last error: {last_exception}")


def _validate_animal_records(animals: List[Dict[str, Any]]) -> None:
    """Validate that animal records have required fields."""
    for animal in animals:
        if not animal.get("Internal-ID"):
            raise ApiError(f"Animal missing required Internal-ID: {animal.get('Name', 'Unknown')}")

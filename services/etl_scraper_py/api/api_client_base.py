"""
Base API client utilities shared across all ShelterLuv API modules.
"""

import os
import time
from typing import Any, Callable, Dict, List

import requests

from errors import ApiError

# Base API configuration
BASE_URL = "https://new.shelterluv.com/api/v1"

# Rate limiting and retry configuration
REQUEST_TIMEOUT = (3, 10)  # (connect, read) timeouts in seconds
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # Exponential backoff: 1s, 2s, 4s
RATE_LIMIT_DELAY = 0.1  # Small delay between requests to be respectful
RATE_LIMIT_BACKOFF_FACTOR = 5  # Longer backoff for rate limits: 5s, 25s, 125s

# Configurable delays between successful requests (not just retries)
# These help avoid hitting rate limits when paginating through large datasets
API_REQUEST_DELAYS = {
    "default": 0.5,  # 500ms between requests by default
    "events": 2.0,  # Events API is particularly heavy, use 2s delay
    "people": 1.5,  # People API also heavy, use 1.5s delay
    "animals": 0.3,  # Animals API is lighter, use 300ms delay
}

# Environment variable to disable rate limiting delays for testing
DISABLE_API_RATE_LIMITING = os.environ.get("DISABLE_API_RATE_LIMITING", "").lower() in (
    "true",
    "1",
    "yes",
)


def make_request_with_retry(
    request_func: Callable[[], requests.Response],
    max_retries: int = MAX_RETRIES,
    rate_limit_backoff_factor: int = RATE_LIMIT_BACKOFF_FACTOR,
    retry_backoff_factor: int = RETRY_BACKOFF_FACTOR,
    rate_limit_delay: float = RATE_LIMIT_DELAY,
) -> Dict[str, Any]:
    """
    Execute a request function with retry logic and rate limiting.

    Args:
        request_func: Function that returns a requests.Response
        max_retries: Maximum number of retry attempts
        rate_limit_backoff_factor: Backoff factor for rate limit errors
        retry_backoff_factor: Backoff factor for general retries
        rate_limit_delay: Delay between retry attempts

    Returns:
        JSON response data

    Raises:
        ApiError: On request failures after all retries
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            # Additional small delay between retry attempts
            if attempt > 0:
                retry_delay = rate_limit_delay * (retry_backoff_factor**attempt)
                time.sleep(retry_delay)

            response = request_func()
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None

            # Handle rate limiting (429) with exponential backoff
            if status_code == 429:
                backoff_time = rate_limit_backoff_factor**attempt
                time.sleep(backoff_time)
                last_exception = e
                continue

            # Don't retry client errors (4xx) except 429
            if status_code and 400 <= status_code < 500 and status_code != 429:
                raise ApiError(f"ShelterLuv API client error ({status_code}): {e}")

            # Retry server errors (5xx) and other issues
            last_exception = e

        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.RequestException,
        ) as e:
            last_exception = e

            if attempt < max_retries - 1:
                backoff_time = retry_backoff_factor**attempt
                time.sleep(backoff_time)
                continue
            else:
                raise ApiError(f"ShelterLuv API request failed after {max_retries} attempts: {e}")

    # If we get here, all retries failed
    raise ApiError(
        f"ShelterLuv API request failed after {max_retries} attempts. Last error: {last_exception}"
    )


def _make_api_request(
    url: str,
    headers: Dict[str, str],
    params: Dict[str, Any] = None,
    max_retries: int = MAX_RETRIES,
    request_delay: float = None,
) -> Dict[str, Any]:
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
        time.sleep(request_delay)

    def request_func() -> requests.Response:
        return requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)

    return make_request_with_retry(request_func, max_retries=max_retries)


def _validate_animal_records(animals: List[Dict[str, Any]]) -> None:
    """Validate that animal records have required fields."""
    for animal in animals:
        if not animal.get("Internal-ID"):
            raise ApiError(f"Animal missing required Internal-ID: {animal.get('Name', 'Unknown')}")

"""
ShelterLuv API client for memo/note-related operations.
"""

from typing import List, Dict, Any, Literal
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from .api_client_base import _make_api_request, BASE_URL
from errors import ApiError

@dataclass
class MemoResult:
    """Result of fetching memos for a dog."""
    internal_id: str
    memos_html: str
    source: Literal["api", "scrape", "none"]
    api_failed: bool = False

def get_animal_memos(api_key: str, internal_id: str) -> MemoResult:
    """
    Fetch memos/notes for a specific animal.

    Args:
        api_key: ShelterLuv API key
        internal_id: Animal's internal ID

    Returns:
        MemoResult with memos HTML content
    """
    headers = {"X-API-Key": api_key}

    try:
        data = _make_api_request(f"{BASE_URL}/animals/{internal_id}/memos", headers)

        memos_html = ""

        # Handle different API response formats for backward compatibility
        if data.get("documents"):
            # Format: {"documents": [{"type": "memo", "content": "..."}, ...]}
            memo_parts = []
            for doc in data["documents"]:
                if doc.get("type") == "memo" and doc.get("content"):
                    memo_parts.append(doc["content"].strip())
            if memo_parts:
                memos_html = "<br>".join(memo_parts)

        elif data.get("memos"):
            if isinstance(data["memos"], str):
                # Format: {"memos": "single memo content"}
                memos_html = data["memos"].strip()
            elif isinstance(data["memos"], list):
                # Format: {"memos": [{"Date": "...", "Content": "..."}, ...]}
                memo_parts = []
                for memo in data["memos"]:
                    if isinstance(memo, dict):
                        date = memo.get("Date", "")
                        content = memo.get("Content", "").strip()
                        if content:
                            if date:
                                memo_parts.append(f"<strong>{date}:</strong> {content}")
                            else:
                                memo_parts.append(content)
                    elif isinstance(memo, str):
                        # Handle string memos in list
                        memo_parts.append(memo.strip())
                if memo_parts:
                    memos_html = "<br>".join(memo_parts)

        return MemoResult(
            internal_id=internal_id,
            memos_html=memos_html,
            source="api",
            api_failed=False
        )

    except ApiError as e:
        return MemoResult(
            internal_id=internal_id,
            memos_html="",
            source="api",
            api_failed=True
        )

def get_animals_memos_batch(api_key: str, internal_ids: List[str]) -> Dict[str, MemoResult]:
    """
    Fetch memos for multiple animals concurrently.

    Args:
        api_key: ShelterLuv API key
        internal_ids: List of animal internal IDs

    Returns:
        Dict mapping internal_id -> MemoResult
    """
    if not internal_ids:
        return {}

    headers = {"X-API-Key": api_key}
    results = {}

    def fetch_memos(internal_id: str) -> MemoResult:
        return get_animal_memos(api_key, internal_id)

    # Use ThreadPoolExecutor for concurrent fetching
    with ThreadPoolExecutor(max_workers=min(5, len(internal_ids))) as executor:
        futures = [executor.submit(fetch_memos, internal_id) for internal_id in internal_ids]

        for future in as_completed(futures):
            result = future.result()
            results[result.internal_id] = result

    return results

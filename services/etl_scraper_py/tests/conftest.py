"""
Pytest configuration and shared fixtures for ETL tests.

Provides consistent test setup, fixtures, and helpers across all ETL test files.
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest  # pyright: ignore[reportMissingImports]

# Add the current directory to Python path so absolute imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules conditionally to avoid relative import issues during pytest loading
try:
    from config import EnvProfile, EtlConfig, SecretsConfig, SecretsMode
    from extract import ExtractResult
    from load import LoadResult
    from transform import TransformConfig, TransformResult
    IMPORTS_SUCCESSFUL = True
except ImportError:
    # If imports fail, we'll skip fixtures that need them
    IMPORTS_SUCCESSFUL = False
    EnvProfile = None
    EtlConfig = None
    SecretsConfig = None
    SecretsMode = None
    ExtractResult = None
    LoadResult = None
    TransformConfig = None
    TransformResult = None


@pytest.fixture
def test_creds():
    """Standard test credentials fixture."""
    return {"api_key": "test_key", "username": "test_user", "password": "test_pass"}


@pytest.fixture
def mock_creds_patch(test_creds):
    """Fixture that patches get_shelterluv_creds to return test credentials."""
    with patch("secret_manager.get_shelterluv_creds", return_value=test_creds) as mock:
        yield mock


@pytest.fixture
def test_config():
    """Standard test EtlConfig fixture."""
    if not IMPORTS_SUCCESSFUL:
        pytest.skip("Required modules could not be imported")
    return EtlConfig(
        env_profile=EnvProfile.DEV,
        project_id="test-project",
        collection_name="dogs_test",
        secrets=SecretsConfig(mode=SecretsMode.ENV, project_id="test-project"),
        memos_mode="api",
        max_concurrent_scrapes=2,
        dry_run=False,
        animal_limit=None,
        skip_events_people=True,
    )


@pytest.fixture
def test_extract_result():
    """Standard test ExtractResult fixture."""
    if not IMPORTS_SUCCESSFUL:
        pytest.skip("Required modules could not be imported")
    return ExtractResult(
        in_custody_ids={"1", "2"},
        animals_by_id={
            "1": {
                "Internal-ID": "1",
                "ID": "A1",
                "Name": "Dog 1",
                "Status": "AVAILABLE",
                "AgeYears": 2.0,
                "AgeDisplay": "2 years",
                "IsInCustody": True,
                "IsAvailableForAdoption": True,
                "IsHospice": False,
                "IsEventDog": False,
            },
            "2": {
                "Internal-ID": "2",
                "ID": "A2",
                "Name": "Dog 2",
                "Status": "AVAILABLE",
                "AgeYears": 3.0,
                "AgeDisplay": "3 years",
                "IsInCustody": True,
                "IsAvailableForAdoption": True,
                "IsHospice": False,
                "IsEventDog": False,
            },
        },
        events=[{"event": "test"}],
        people=[{"person": "test"}],
        existing_metadata={},
        memos_data={"1": "<html>memo1</html>", "2": "<html>memo2</html>"},
        scraped_map={"1": {"profile": "data1"}, "2": {"profile": "data2"}},
    )


@pytest.fixture
def test_transform_config():
    """Standard test TransformConfig fixture."""
    if not IMPORTS_SUCCESSFUL:
        pytest.skip("Required modules could not be imported")
    return TransformConfig()


@pytest.fixture
def test_transform_result():
    """Standard test TransformResult fixture."""
    if not IMPORTS_SUCCESSFUL:
        pytest.skip("Required modules could not be imported")
    return TransformResult(
        dogs=[
            {
                "Internal-ID": "1",
                "ID": "A1",
                "Name": "Dog 1",
                "Status": "AVAILABLE",
                "AgeYears": 2.0,
                "AgeDisplay": "2 years",
                "IsInCustody": True,
                "IsAvailableForAdoption": True,
                "IsHospice": False,
                "IsEventDog": False,
            },
            {
                "Internal-ID": "2",
                "ID": "A2",
                "Name": "Dog 2",
                "Status": "AVAILABLE",
                "AgeYears": 3.0,
                "AgeDisplay": "3 years",
                "IsInCustody": True,
                "IsAvailableForAdoption": True,
                "IsHospice": False,
                "IsEventDog": False,
            },
        ],
        invalid_count=0,
        scraped_count=2,
        skipped_count=0,
    )


@pytest.fixture
def test_load_result():
    """Standard test LoadResult fixture."""
    if not IMPORTS_SUCCESSFUL:
        pytest.skip("Required modules could not be imported")
    return LoadResult(dogs_written=2, dogs_deleted=0)


@pytest.fixture(autouse=True)
def setup_test_env():
    """Automatically set up test environment for all tests."""
    # Set test environment to avoid using production data
    os.environ["FIRESTORE_TEST_MODE"] = "true"
    # Ensure we don't accidentally use real credentials
    os.environ["DISABLE_SECRET_MANAGER"] = "1"
    yield
    # Cleanup is handled automatically by pytest


@pytest.fixture
def parser():
    """
    Parser fixture for testing memo parsing helper functions.
    Provides access to pure functions from scraper.parsers module.
    """
    from scraper.parsers import (
        INTAKE_KEYWORDS,
        MEDICAL_KEYWORDS,
        PERSONALITY_KEYWORDS,
        _categorize_memo_section_pure,
        _clean_memo_html_pure,
        _count_keywords_pure,
        _split_memo_into_sections_pure,
    )

    # Create a simple object that wraps the pure functions
    class ParserWrapper:
        def _clean_memo_html(self, html):
            return _clean_memo_html_pure(html)

        def _split_memo_into_sections(self, text):
            return _split_memo_into_sections_pure(text)

        def _count_keywords(self, text, keywords):
            return _count_keywords_pure(text, keywords)

        def _categorize_memo_section(self, section_lower):
            return _categorize_memo_section_pure(section_lower)

        def _get_personality_keywords(self):
            return PERSONALITY_KEYWORDS

        def _get_intake_keywords(self):
            return INTAKE_KEYWORDS

        def _get_medical_keywords(self):
            return MEDICAL_KEYWORDS

    return ParserWrapper()

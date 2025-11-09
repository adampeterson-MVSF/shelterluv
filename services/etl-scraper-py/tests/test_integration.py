"""
Integration tests for ETL pipeline components.
Tests internal component integration with mocked external dependencies.
"""

import pytest
import os
from unittest.mock import patch, Mock
import pipeline
from extract import ExtractResult
from errors import ApiError
from config import EtlConfig, SecretsConfig, SecretsMode, EnvProfile


class TestETLIntegration:
    """Integration tests for ETL pipeline components with mocked external dependencies."""

    @classmethod
    def setup_class(cls):
        """Set up test environment."""
        # Set test environment to avoid using production data
        os.environ["FIRESTORE_TEST_MODE"] = "true"

    @classmethod
    def teardown_class(cls):
        """Clean up test environment."""
        pass

    def setup_method(self):
        """Set up before each test."""
        pass

    def _create_test_config(self, dry_run=False, animal_limit=None):
        """Create a test EtlConfig for testing."""
        return EtlConfig(
            env_profile=EnvProfile.DEV,
            project_id="test-project",
            collection_name="dogs_test",
            secrets=SecretsConfig(mode=SecretsMode.ENV, project_id="test-project"),
            memos_mode="api",
            max_concurrent_scrapes=2,
            dry_run=dry_run,
            animal_limit=animal_limit
        )

    @patch('secret_manager.get_shelterluv_creds')
    @patch('api.api_client_events.get_animal_events')
    @patch('api.api_client_people.get_people')
    @patch('scraper.ShelterLuvScraper.scrape_profile_only')
    @patch('db.write_dogs')
    @patch('db.purge_stale_dogs')
    @patch('db.get_db')
    def test_full_etl_pipeline_integration(self, mock_get_db, mock_purge_stale, mock_write_dogs, mock_scrape_details, mock_get_people, mock_get_events, mock_creds):
        """Test the complete ETL pipeline with Firestore emulator."""

        # Setup mocks
        mock_creds.return_value = {
            "api_key": "test_key",
            "username": "test_user",
            "password": "test_pass"
        }

        # Mock database operations
        mock_write_dogs.return_value = {"dogs_written": 2, "dogs_invalid": 0}
        mock_purge_stale.return_value = 0  # Returns int, not dict
        mock_get_db.return_value = None  # Mock firestore client

        # Mock API responses
        mock_get_events.return_value = [
            {
                "Internal-ID": "1",
                "EventType": "Adoption",
                "EventDate": "2024-01-15",
                "Outcome": "Adopted"
            }
        ]

        mock_get_people.return_value = [
            {
                "ID": "P1",
                "Name": "John Foster",
                "Type": "Foster"
            }
        ]

        # Mock scraping results
        mock_scrape_details.return_value = {
            "FullAnimalProfile": "Headquarters Available - Friendly dog", # <-- ADD THIS
            "AdoptionCategory": "Adult",
            "MedicalCategory": "Healthy",
            "BehaviorCategory": "Good with kids",
            "MemosRawHTML": "<p>Well socialized and friendly</p>",
            "IsAvailableForAdoption": True,
            "IsInCustody": True,
            "IsHospice": False,
            "IsEventDog": False
        }

        # Mock the animal extraction to return test data
        test_animals_by_id = {
            "1": {
                "Internal-ID": "1",
                "ID": "A1",
                "Name": "Buddy",
                "Status": "AVAILABLE",
                "Age": "3 years",
                "Size": "Medium",
                "Breed": "Golden Retriever"
            },
            "2": {
                "Internal-ID": "2",
                "ID": "A2",
                "Name": "Max",
                "Status": "PENDING",
                "Age": "2 years",
                "Size": "Large",
                "Breed": "Labrador"
            }
        }

        test_extract_result = ExtractResult(
            in_custody_ids={"1", "2"},
            animals_by_id=test_animals_by_id,
            events=[{"ID": "1", "Type": "Intake", "Date": "2024-01-01"}],
            people=[{"ID": "1", "Name": "John Doe"}],
            existing_metadata={}
        )

        with patch('pipeline.extract', return_value=test_extract_result):
            # Run the ETL process (dry run to avoid database operations)
            config = self._create_test_config(dry_run=True, animal_limit=3)
            stats = pipeline.run_etl_process(config)

            # Verify stats
            assert stats["total_animals_fetched"] == 2
            assert stats["total_events_fetched"] == 1
            assert stats["total_people_fetched"] == 1
            assert stats["dogs_processed"] == 2
            assert stats["dogs_written"] == 2  # Dry run simulates the writes
            assert stats["dogs_deleted"] == 0  # Dry run, so no actual deletes

            # Verify database operations were called (dry run still simulates)
            mock_write_dogs.assert_called_once()
            mock_purge_stale.assert_called_once()

    @patch('secret_manager.get_shelterluv_creds')
    @patch('db.write_dogs')
    @patch('db.purge_stale_dogs')
    @patch('db.get_db')
    def test_etl_pipeline_with_api_failures(self, mock_get_db, mock_purge_stale, mock_write_dogs, mock_creds):
        """Test ETL pipeline handles API failures gracefully and still writes valid data."""

        mock_creds.return_value = {
            "api_key": "test_key",
            "username": "test_user",
            "password": "test_pass"
        }

        # Mock database operations
        mock_write_dogs.return_value = {"dogs_written": 1, "dogs_invalid": 0}
        mock_purge_stale.return_value = 0  # Returns int, not dict
        mock_get_db.return_value = None  # Mock firestore client

        test_animals_by_id = {
            "1": {
                "Internal-ID": "1",
                "ID": "A1",
                "Name": "Buddy",
                "Status": "AVAILABLE",
                "Age": "3 years"
            }
        }

        test_extract_result = ExtractResult(
            in_custody_ids={"1"},
            animals_by_id=test_animals_by_id,
            events=[],  # Will be overridden by API error
            people=[],  # Will be overridden by API error
            existing_metadata={},
            events_failed=True,  # Simulate events API failure
            people_failed=True   # Simulate people API failure
        )

        with patch('pipeline.extract', return_value=test_extract_result), \
             patch('api.api_client_events.get_animal_events', side_effect=ApiError("Events API down")), \
             patch('api.api_client_people.get_people', side_effect=ApiError("People API down")), \
             patch('scraper.ShelterLuvScraper.scrape_dog_details', return_value={
                 "FullAnimalProfile": "Headquarters Available - Friendly dog", # <-- ADD THIS
                 "AdoptionCategory": "",
                 "MedicalCategory": "",
                 "BehaviorCategory": "",
                 "MemosRawHTML": "",
                 "IsAvailableForAdoption": True,
                 "IsInCustody": True,
                 "IsHospice": False,
                 "IsEventDog": False
             }):
            # Run ETL process (dry run)
            config = self._create_test_config(dry_run=True)
            stats = pipeline.run_etl_process(config)

            # Should still process the dog despite API failures
            assert stats["total_animals_fetched"] == 1
            assert stats["total_events_fetched"] == 0  # API failed
            assert stats["total_people_fetched"] == 0  # API failed
            assert stats["dogs_processed"] == 1
            assert stats["dogs_written"] == 1  # Dry run simulates the writes
            assert "events_fetch_failed" in stats
            assert "people_fetch_failed" in stats

            # Verify database operations were called (dry run still simulates)
            mock_write_dogs.assert_called_once()
            mock_purge_stale.assert_called_once()

    @patch('secret_manager.get_shelterluv_creds')
    @patch('db.purge_stale_dogs')
    @patch('db.get_db')
    def test_etl_pipeline_no_animals_early_exit(self, mock_get_db, mock_purge_stale, mock_creds):
        """Test ETL pipeline exits early when no animals are available."""

        mock_creds.return_value = {
            "api_key": "test_key",
            "username": "test_user",
            "password": "test_pass"
        }

        # Mock database operations
        mock_purge_stale.return_value = 5  # Simulate purging stale dogs (returns int)
        mock_get_db.return_value = None  # Mock firestore client

        empty_extract_result = ExtractResult(
            in_custody_ids=set(),
            animals_by_id={},
            events=[],
            people=[],
            existing_metadata={}
        )

        with patch('pipeline.extract', return_value=empty_extract_result):
            config = self._create_test_config(dry_run=True)
            stats = pipeline.run_etl_process(config)

            # Should exit early
            assert stats["total_animals_fetched"] == 0
            assert stats["dogs_deleted"] == 0  # Dry run, so no actual deletes
            assert stats["dogs_processed"] == 0
            assert stats["dogs_written"] == 0

            # Verify database operations were NOT called (no dogs to process in dry run)
            mock_purge_stale.assert_not_called()


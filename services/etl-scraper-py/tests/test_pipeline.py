"""
Tests for pipeline.py - ETL orchestration and process flow.
Tests that all ETL steps are called in the correct order and handle edge cases.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pipeline import run_etl_process, compute_stats, ExtractResult, TransformResult, LoadResult, TransformConfig, PipelineStats
from extract import extract
from transform import transform
from load import load
from errors import ApiError


class TestIncrementalScraping:
    """Test incremental ETL functionality within transform."""

    @patch('transform.ShelterLuvScraper')
    def test_transform_skips_unchanged_dogs(self, mock_scraper_class):
        """Test that transform skips dogs that haven't changed."""
        mock_scraper = Mock()
        mock_scraper.scrape_profile_only.return_value = {"scraped": "data"}
        mock_scraper.__enter__ = Mock(return_value=mock_scraper)
        mock_scraper.__exit__ = Mock(return_value=None)
        mock_scraper_class.return_value = mock_scraper

        # Setup extract result with existing metadata
        extract_result = ExtractResult(
            in_custody_ids={"1", "2"},
            animals_by_id={
                "1": {"Internal-ID": "1", "ID": "A1", "Name": "Dog 1", "Status": "AVAILABLE", "AgeYears": 2.0, "AgeDisplay": "2 years", "IsInCustody": True, "IsAvailableForAdoption": True, "IsHospice": False, "IsEventDog": False, "SourceUpdatedAt": "2024-01-01T10:00:00Z"},
                "2": {"Internal-ID": "2", "ID": "A2", "Name": "Dog 2", "Status": "AVAILABLE", "AgeYears": 3.0, "AgeDisplay": "3 years", "IsInCustody": True, "IsAvailableForAdoption": True, "IsHospice": False, "IsEventDog": False, "SourceUpdatedAt": "2024-01-01T10:00:00Z"}
            },
            events=[],
            people=[],
            existing_metadata={
                "1": {"source_updated_at": "2024-01-01T10:00:00Z"},  # Same timestamp - unchanged
                "2": {"source_updated_at": "2024-01-01T09:00:00Z"}   # Older timestamp - changed
            }
        )

        creds = {"username": "test", "password": "test"}
        config = TransformConfig(memos_mode="none", max_concurrent_scrapes=1)

        # Mock scraper to return data for dog 2 only
        mock_scraper.scrape_profile_only.return_value = {"scraped": "data"}

        with patch('api_client_memos.get_animals_memos_batch', return_value={}), \
             patch('foster_mapping.build_foster_maps', return_value={}), \
             patch('foster_mapping.build_event_maps', return_value={}), \
             patch('enrichment.build_dog_record') as mock_build_dog:

            mock_build_dog.return_value = {"Internal-ID": "1", "ID": "A1", "Name": "Dog 1", "Status": "AVAILABLE", "AgeYears": 2.0, "AgeDisplay": "2 years", "IsInCustody": True, "IsAvailableForAdoption": True, "IsHospice": False, "IsEventDog": False}

            result = transform(extract_result, creds, config)

            # Should only scrape dog 2 (the changed one), but process both dogs
            assert result.scraped_count == 1
            assert result.skipped_count == 1
            assert len(result.dogs) == 2  # Both dogs are processed

            # Verify scraper was called once for dog 2
            mock_scraper.scrape_profile_only.assert_called_once_with("A2")

    @patch('transform.ShelterLuvScraper')
    def test_transform_scrapes_all_when_no_metadata(self, mock_scraper_class):
        """Test that transform scrapes all dogs when no existing metadata."""
        mock_scraper = Mock()
        mock_scraper.scrape_profile_only.return_value = {"scraped": "data"}
        mock_scraper.__enter__ = Mock(return_value=mock_scraper)
        mock_scraper.__exit__ = Mock(return_value=None)
        mock_scraper_class.return_value = mock_scraper

        # Setup extract result with no existing metadata
        extract_result = ExtractResult(
            in_custody_ids={"1", "2"},
            animals_by_id={
                "1": {"Internal-ID": "1", "ID": "A1", "Name": "Dog 1", "Status": "AVAILABLE", "AgeYears": 2.0, "AgeDisplay": "2 years", "IsInCustody": True, "IsAvailableForAdoption": True, "IsHospice": False, "IsEventDog": False, "SourceUpdatedAt": "2024-01-01T10:00:00Z"},
                "2": {"Internal-ID": "2", "ID": "A2", "Name": "Dog 2", "Status": "AVAILABLE", "AgeYears": 3.0, "AgeDisplay": "3 years", "IsInCustody": True, "IsAvailableForAdoption": True, "IsHospice": False, "IsEventDog": False, "SourceUpdatedAt": "2024-01-01T10:00:00Z"}
            },
            events=[],
            people=[],
            existing_metadata={}  # No existing metadata
        )

        creds = {"username": "test", "password": "test"}
        config = TransformConfig(memos_mode="none", max_concurrent_scrapes=1)

        # Mock scraper to return data
        mock_scraper.scrape_profile_only.return_value = {"scraped": "data"}

        with patch('api_client_memos.get_animals_memos_batch', return_value={}), \
             patch('foster_mapping.build_foster_maps', return_value={}), \
             patch('foster_mapping.build_event_maps', return_value={}), \
             patch('enrichment.build_dog_record') as mock_build_dog:

            mock_build_dog.return_value = {"Internal-ID": "1", "Name": "Dog 1"}

            result = transform(extract_result, creds, config)

            # Should scrape both dogs when no metadata
            assert result.scraped_count == 2
            assert result.skipped_count == 0
            assert len(result.dogs) == 2  # Both dogs are processed

            # Verify scraper was called twice
            assert mock_scraper.scrape_profile_only.call_count == 2

    @patch('transform.ShelterLuvScraper')
    def test_transform_concurrent_mode(self, mock_scraper_class):
        """Test that transform uses concurrent scraping when max_concurrent_scrapes > 1."""
        # Create mock scraper instances that support context manager protocol
        scraper_instances = []
        for i in range(2):  # Need exactly 2 scrapers for 2 concurrent chunks
            mock_scraper = Mock()
            mock_scraper.scrape_profile_only.return_value = {"scraped": f"data_{i}"}
            # Make it a proper context manager
            mock_scraper.__enter__ = Mock(return_value=mock_scraper)
            mock_scraper.__exit__ = Mock(return_value=None)
            scraper_instances.append(mock_scraper)

        # Return different scraper instances for each call
        mock_scraper_class.side_effect = scraper_instances

        # Setup extract result with 4 dogs to trigger concurrent processing
        extract_result = ExtractResult(
            in_custody_ids={"1", "2", "3", "4"},
            animals_by_id={
                "1": {"Internal-ID": "1", "ID": "A1", "Name": "Dog 1", "Status": "AVAILABLE", "AgeYears": 2.0, "AgeDisplay": "2 years", "IsInCustody": True, "IsAvailableForAdoption": True, "IsHospice": False, "IsEventDog": False, "SourceUpdatedAt": "2024-01-01T10:00:00Z"},
                "2": {"Internal-ID": "2", "ID": "A2", "Name": "Dog 2", "Status": "AVAILABLE", "AgeYears": 3.0, "AgeDisplay": "3 years", "IsInCustody": True, "IsAvailableForAdoption": True, "IsHospice": False, "IsEventDog": False, "SourceUpdatedAt": "2024-01-01T10:00:00Z"},
                "3": {"Internal-ID": "3", "ID": "A3", "Name": "Dog 3", "Status": "AVAILABLE", "AgeYears": 1.0, "AgeDisplay": "1 year", "IsInCustody": True, "IsAvailableForAdoption": True, "IsHospice": False, "IsEventDog": False, "SourceUpdatedAt": "2024-01-01T10:00:00Z"},
                "4": {"Internal-ID": "4", "ID": "A4", "Name": "Dog 4", "Status": "AVAILABLE", "AgeYears": 4.0, "AgeDisplay": "4 years", "IsInCustody": True, "IsAvailableForAdoption": True, "IsHospice": False, "IsEventDog": False, "SourceUpdatedAt": "2024-01-01T10:00:00Z"}
            },
            events=[],
            people=[],
            existing_metadata={}  # No existing metadata
        )

        creds = {"username": "test", "password": "test"}
        config = TransformConfig(memos_mode="none", max_concurrent_scrapes=2)

        with patch('api_client_memos.get_animals_memos_batch', return_value={}), \
             patch('foster_mapping.build_foster_maps', return_value={}), \
             patch('foster_mapping.build_event_maps', return_value={}), \
             patch('enrichment.build_dog_record') as mock_build_dog:

            mock_build_dog.return_value = {"Internal-ID": "1", "Name": "Dog 1"}

            result = transform(extract_result, creds, config)

            # Should scrape all 4 dogs concurrently (2 chunks of 2 each)
            assert result.scraped_count == 4
            assert result.skipped_count == 0
            assert len(result.dogs) == 4  # All dogs are processed

            # Should have created 2 scraper instances for concurrent chunks
            assert mock_scraper_class.call_count == 2


class TestPipelineOrchestration:
    """Test the ETL pipeline orchestration."""

    @patch('secret_manager.get_shelterluv_creds')
    @patch('db.get_db')
    @patch('pipeline.extract')
    @patch('pipeline.transform')
    @patch('pipeline.load')
    @patch('pipeline.compute_stats')
    def test_run_etl_process_full_flow_success(self, mock_compute_stats, mock_load, mock_transform, mock_extract, mock_get_db, mock_creds):
        """Test successful full ETL process execution."""
        # Setup mocks
        mock_creds.return_value = {"api_key": "test_key", "username": "test", "password": "test"}

        # Mock extract result
        extract_result = ExtractResult(
            in_custody_ids={"1", "2"},
            animals_by_id={
                "1": {"Internal-ID": "1", "ID": "A1", "Name": "Dog 1", "Status": "AVAILABLE", "AgeYears": 2.0, "AgeDisplay": "2 years", "IsInCustody": True, "IsAvailableForAdoption": True, "IsHospice": False, "IsEventDog": False},
                "2": {"Internal-ID": "2", "ID": "A2", "Name": "Dog 2", "Status": "AVAILABLE", "AgeYears": 3.0, "AgeDisplay": "3 years", "IsInCustody": True, "IsAvailableForAdoption": True, "IsHospice": False, "IsEventDog": False}
            },
            events=[{"event": "test"}],
            people=[{"person": "test"}],
            existing_metadata={}
        )
        mock_extract.return_value = extract_result

        # Mock transform result
        transform_result = TransformResult(
            dogs=[
                {"Internal-ID": "1", "ID": "A1", "Name": "Dog 1", "Status": "AVAILABLE", "AgeYears": 2.0, "AgeDisplay": "2 years", "IsInCustody": True, "IsAvailableForAdoption": True, "IsHospice": False, "IsEventDog": False},
                {"Internal-ID": "2", "ID": "A2", "Name": "Dog 2", "Status": "AVAILABLE", "AgeYears": 3.0, "AgeDisplay": "3 years", "IsInCustody": True, "IsAvailableForAdoption": True, "IsHospice": False, "IsEventDog": False}
            ],
            invalid_count=0,
            scraped_count=2,
            skipped_count=0
        )
        mock_transform.return_value = transform_result

        # Mock load result
        load_result = LoadResult(dogs_written=5, dogs_deleted=2)
        mock_load.return_value = load_result

        # Mock final stats
        mock_compute_stats.return_value = PipelineStats(
            num_in_custody_ids=2,
            num_animals_fetched_from_api=2,
            total_events_fetched=1,
            total_people_fetched=1,
            dogs_processed=2,
            dogs_scraped=2,
            dogs_written=5,
            dogs_deleted=2
        )

        # Run the ETL process
        stats = run_etl_process(dry_run=False)

        # Verify credentials were fetched
        mock_creds.assert_called_once()
        mock_extract.assert_called_once_with({"api_key": "test_key", "username": "test", "password": "test"}, None)

        # Verify transform was called with correct config
        mock_transform.assert_called_once()
        args, kwargs = mock_transform.call_args
        assert args[0] == extract_result
        assert args[1] == {"api_key": "test_key", "username": "test", "password": "test"}
        assert args[2].memos_mode == "api"
        assert args[2].max_concurrent_scrapes == 2

        # Verify load was called
        mock_load.assert_called_once_with(transform_result, False)

        # Verify compute_stats was called
        mock_compute_stats.assert_called_once_with(extract_result, transform_result, load_result)

        # Verify final stats structure
        assert stats["num_in_custody_ids"] == 2
        assert stats["num_animals_fetched_from_api"] == 2
        assert stats["total_events_fetched"] == 1
        assert stats["total_people_fetched"] == 1
        assert stats["dogs_processed"] == 2
        assert stats["dogs_scraped"] == 2
        assert stats["dogs_written"] == 5
        assert stats["dogs_deleted"] == 2

    @patch('secret_manager.get_shelterluv_creds')
    @patch('db.get_db')
    @patch('pipeline.extract')
    @patch('pipeline.load')
    @patch('pipeline.compute_stats')
    def test_run_etl_process_no_animals_early_exit(self, mock_compute_stats, mock_load, mock_extract, mock_get_db, mock_creds):
        """Test ETL process exits early when no animals are in custody."""
        # Setup mocks
        mock_creds.return_value = {"api_key": "test_key", "username": "test", "password": "test"}

        # Mock extract result with no animals
        extract_result = ExtractResult(
            in_custody_ids=set(),
            animals_by_id={},
            events=[],
            people=[],
            existing_metadata={}
        )
        mock_extract.return_value = extract_result

        # Mock load result for empty case
        load_result = LoadResult(dogs_written=0, dogs_deleted=10)
        mock_load.return_value = load_result

        # Mock final stats
        mock_compute_stats.return_value = PipelineStats(
            num_in_custody_ids=0,
            num_animals_fetched_from_api=0,
            dogs_deleted=10
        )

        stats = run_etl_process(dry_run=False)

        # Verify extract was called
        mock_extract.assert_called_once_with({"api_key": "test_key", "username": "test", "password": "test"}, None)

        # Verify load was called with empty transform result and no dry_run
        mock_load.assert_called_once()
        args, kwargs = mock_load.call_args
        assert args[0].dogs == []  # Empty transform result
        assert args[0].invalid_count == 0
        assert args[0].scraped_count == 0
        assert args[0].skipped_count == 0
        assert args[1] == False  # dry_run=False

        # Verify stats
        assert stats["num_in_custody_ids"] == 0
        assert stats["num_animals_fetched_from_api"] == 0
        assert stats["dogs_deleted"] == 10

    @patch('secret_manager.get_shelterluv_creds')
    @patch('db.get_db')
    @patch('pipeline.extract')
    @patch('pipeline.transform')
    @patch('pipeline.load')
    @patch('pipeline.compute_stats')
    def test_run_etl_process_events_fetch_failure(self, mock_compute_stats, mock_load, mock_transform, mock_extract, mock_get_db, mock_creds):
        """Test ETL process handles events API failure gracefully."""
        # Setup mocks
        mock_creds.return_value = {"api_key": "test_key", "username": "test", "password": "test"}

        # Mock extract result with events failure
        extract_result = ExtractResult(
            in_custody_ids={"1"},
            animals_by_id={"1": {"Internal-ID": "1", "ID": "A1", "Name": "Dog 1"}},
            events=[],  # Empty due to failure
            people=[{"person": "test"}],  # People succeeded
            existing_metadata={},
            events_failed=True,  # Events failed
            people_failed=False
        )
        mock_extract.return_value = extract_result

        # Mock transform result
        transform_result = TransformResult(
            dogs=[{"Internal-ID": "1"}],
            invalid_count=0,
            scraped_count=1,
            skipped_count=0
        )
        mock_transform.return_value = transform_result

        # Mock load result
        load_result = LoadResult(dogs_written=3, dogs_deleted=1)
        mock_load.return_value = load_result

        # Mock final stats
        mock_compute_stats.return_value = PipelineStats(
            num_in_custody_ids=1,
            num_animals_fetched_from_api=1,
            total_events_fetched=0,
            total_people_fetched=1,
            dogs_processed=1,
            dogs_scraped=1,
            dogs_written=3,
            dogs_deleted=1,
            events_fetch_failed=True,
            people_fetch_failed=False
        )

        stats = run_etl_process(dry_run=False)

        # Verify extract was called
        mock_extract.assert_called_once_with({"api_key": "test_key", "username": "test", "password": "test"}, None)

        # Verify transform was called with extract result containing failed events
        mock_transform.assert_called_once()
        args, kwargs = mock_transform.call_args
        assert args[0] == extract_result
        assert len(args[0].events) == 0  # Empty events due to failure

        # Verify stats reflect the failure
        assert stats["num_in_custody_ids"] == 1
        assert stats["num_animals_fetched_from_api"] == 1
        assert stats["total_events_fetched"] == 0
        assert stats["total_people_fetched"] == 1
        assert stats["events_fetch_failed"] == True
        assert stats["people_fetch_failed"] == False

    @patch('secret_manager.get_shelterluv_creds')
    @patch('db.get_db')
    @patch('pipeline.extract')
    @patch('pipeline.transform')
    @patch('pipeline.load')
    @patch('pipeline.compute_stats')
    def test_run_etl_process_people_fetch_failure(self, mock_compute_stats, mock_load, mock_transform, mock_extract, mock_get_db, mock_creds):
        """Test ETL process handles people API failure gracefully."""
        # Setup mocks
        mock_creds.return_value = {"api_key": "test_key", "username": "test", "password": "test"}

        # Mock extract result with people failure
        extract_result = ExtractResult(
            in_custody_ids={"1"},
            animals_by_id={"1": {"Internal-ID": "1", "ID": "A1", "Name": "Dog 1"}},
            events=[{"event": "test"}],  # Events succeeded
            people=[],  # Empty due to failure
            existing_metadata={},
            events_failed=False,
            people_failed=True  # People failed
        )
        mock_extract.return_value = extract_result

        # Mock transform result
        transform_result = TransformResult(
            dogs=[{"Internal-ID": "1"}],
            invalid_count=0,
            scraped_count=1,
            skipped_count=0
        )
        mock_transform.return_value = transform_result

        # Mock load result
        load_result = LoadResult(dogs_written=2, dogs_deleted=0)
        mock_load.return_value = load_result

        # Mock final stats
        mock_compute_stats.return_value = PipelineStats(
            num_in_custody_ids=1,
            num_animals_fetched_from_api=1,
            total_events_fetched=1,
            total_people_fetched=0,
            dogs_processed=1,
            dogs_scraped=1,
            dogs_written=2,
            dogs_deleted=0,
            events_fetch_failed=False,
            people_fetch_failed=True
        )

        stats = run_etl_process(dry_run=False)

        # Verify extract was called
        mock_extract.assert_called_once_with({"api_key": "test_key", "username": "test", "password": "test"}, None)

        # Verify transform was called with extract result containing failed people
        mock_transform.assert_called_once()
        args, kwargs = mock_transform.call_args
        assert args[0] == extract_result
        assert len(args[0].people) == 0  # Empty people due to failure

        # Verify stats reflect the failure
        assert stats["total_events_fetched"] == 1
        assert stats["total_people_fetched"] == 0
        assert stats["events_fetch_failed"] == False
        assert stats["people_fetch_failed"] == True

    @patch('secret_manager.get_shelterluv_creds')
    @patch('db.get_db')
    @patch('pipeline.extract')
    @patch('pipeline.transform')
    @patch('pipeline.load')
    @patch('pipeline.compute_stats')
    def test_run_etl_process_dry_run_flag(self, mock_compute_stats, mock_load, mock_transform, mock_extract, mock_get_db, mock_creds):
        """Test that dry_run flag is properly passed through to load function."""
        # Setup mocks
        mock_creds.return_value = {"api_key": "test_key", "username": "test", "password": "test"}

        # Mock extract result
        extract_result = ExtractResult(
            in_custody_ids={"1"},
            animals_by_id={"1": {"Internal-ID": "1", "ID": "A1", "Name": "Dog 1"}},
            events=[],
            people=[],
            existing_metadata={}
        )
        mock_extract.return_value = extract_result

        # Mock transform result
        transform_result = TransformResult(
            dogs=[{"Internal-ID": "1"}],
            invalid_count=0,
            scraped_count=1,
            skipped_count=0
        )
        mock_transform.return_value = transform_result

        # Mock load result
        load_result = LoadResult(dogs_written=1, dogs_deleted=0)
        mock_load.return_value = load_result

        # Mock final stats
        mock_compute_stats.return_value = PipelineStats(
            num_in_custody_ids=1,
            num_animals_fetched_from_api=1,
            total_events_fetched=0,
            total_people_fetched=0,
            dogs_processed=1,
            dogs_scraped=1,
            dogs_written=1,
            dogs_deleted=0
        )

        # Run with dry_run=True
        stats = run_etl_process(dry_run=True)

        # Verify load was called with dry_run=True
        mock_load.assert_called_once_with(transform_result, True)

    @patch('secret_manager.get_shelterluv_creds')
    @patch('db.get_db')
    @patch('pipeline.extract')
    @patch('pipeline.transform')
    @patch('pipeline.load')
    @patch('pipeline.compute_stats')
    def test_run_etl_process_both_api_failures(self, mock_compute_stats, mock_load, mock_transform, mock_extract, mock_get_db, mock_creds):
        """Test ETL process handles both API failures gracefully."""
        # Setup mocks
        mock_creds.return_value = {"api_key": "test_key", "username": "test", "password": "test"}

        # Mock extract result with both failures
        extract_result = ExtractResult(
            in_custody_ids={"1"},
            animals_by_id={"1": {"Internal-ID": "1", "ID": "A1", "Name": "Dog 1"}},
            events=[],  # Empty due to failure
            people=[],  # Empty due to failure
            existing_metadata={},
            events_failed=True,  # Events failed
            people_failed=True   # People failed
        )
        mock_extract.return_value = extract_result

        # Mock transform result
        transform_result = TransformResult(
            dogs=[{"Internal-ID": "1"}],
            invalid_count=0,
            scraped_count=1,
            skipped_count=0
        )
        mock_transform.return_value = transform_result

        # Mock load result
        load_result = LoadResult(dogs_written=1, dogs_deleted=0)
        mock_load.return_value = load_result

        # Mock final stats
        mock_compute_stats.return_value = PipelineStats(
            num_in_custody_ids=1,
            num_animals_fetched_from_api=1,
            total_events_fetched=0,
            total_people_fetched=0,
            dogs_processed=1,
            dogs_scraped=1,
            dogs_written=1,
            dogs_deleted=0,
            events_fetch_failed=True,
            people_fetch_failed=True
        )

        stats = run_etl_process(dry_run=False)

        # Verify extract was called
        mock_extract.assert_called_once_with({"api_key": "test_key", "username": "test", "password": "test"}, None)

        # Verify transform was called with extract result containing both failures
        mock_transform.assert_called_once()
        args, kwargs = mock_transform.call_args
        assert args[0] == extract_result
        assert len(args[0].events) == 0  # Empty events due to failure
        assert len(args[0].people) == 0  # Empty people due to failure

        # Verify stats reflect both failures
        assert stats["total_events_fetched"] == 0
        assert stats["total_people_fetched"] == 0
        assert stats["events_fetch_failed"] == True
        assert stats["people_fetch_failed"] == True

"""
Tests for pipeline orchestration - overall ETL process flow and coordination.
Tests that all ETL steps are called in the correct order and handle edge cases.
"""

from unittest.mock import patch

import pytest

from config import EnvProfile, EtlConfig, SecretsConfig, SecretsMode
from pipeline import (
    ExtractResult,
    LoadResult,
    PipelineStats,
    TransformConfig,
    TransformResult,
    compute_stats,
    run_etl_process,
)
from transform import transform


class TestPipelineOrchestration:
    """Test the ETL pipeline orchestration."""

    @patch("pipeline.extract")
    @patch("pipeline.transform")
    @patch("pipeline.load")
    @patch("pipeline.compute_stats")
    def test_run_etl_process_full_flow_success(
        self, mock_compute_stats, mock_load, mock_transform, mock_extract
    ):
        """Test successful full ETL process execution."""

        # Mock extract result
        extract_result = ExtractResult(
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
            memos_data={},
            scraped_map={},
        )
        mock_extract.return_value = extract_result

        # Mock transform result
        transform_result = TransformResult(
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
            dogs_deleted=2,
        )

        # Run the ETL process
        config = EtlConfig(
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
        creds = {"api_key": "test_key", "username": "test", "password": "test"}
        stats = run_etl_process(config, creds)

        # Verify extract was called with correct 2-arg signature
        mock_extract.assert_called_once()
        (actual_creds, actual_cfg), _ = mock_extract.call_args
        assert actual_creds == creds
        assert isinstance(actual_cfg, ExtractConfig)
        assert actual_cfg.memos_mode == "api"
        assert actual_cfg.max_concurrent_scrapes == 2
        assert actual_cfg.dry_run == config.dry_run
        assert actual_cfg.skip_events_people == config.skip_events_people

        # Verify transform was called with correct arguments
        mock_transform.assert_called_once()
        args, kwargs = mock_transform.call_args
        assert args[0] == extract_result
        assert args[1] == {"api_key": "test_key", "username": "test", "password": "test"}
        assert isinstance(args[2], TransformConfig)

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

    @patch("pipeline.extract")
    @patch("pipeline.load")
    @patch("pipeline.compute_stats")
    def test_run_etl_process_no_animals_early_exit(
        self, mock_compute_stats, mock_load, mock_extract
    ):
        """Test ETL process exits early when no animals are in custody."""

        # Mock extract result with no animals
        extract_result = ExtractResult(
            in_custody_ids=set(),
            animals_by_id={},
            events=[],
            people=[],
            existing_metadata={},
            memos_data={},
            scraped_map={},
        )
        mock_extract.return_value = extract_result

        # Mock load result for empty case
        load_result = LoadResult(dogs_written=0, dogs_deleted=10)
        mock_load.return_value = load_result

        # Mock final stats
        mock_compute_stats.return_value = PipelineStats(
            num_in_custody_ids=0, num_animals_fetched_from_api=0, dogs_deleted=10
        )

        config = EtlConfig(
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
        creds = {"api_key": "test_key", "username": "test", "password": "test"}
        stats = run_etl_process(config, creds)

        # Verify extract was called with correct 2-arg signature
        mock_extract.assert_called_once()
        (actual_creds, actual_cfg), _ = mock_extract.call_args
        assert actual_creds == creds
        assert isinstance(actual_cfg, ExtractConfig)
        assert actual_cfg.memos_mode == "api"
        assert actual_cfg.max_concurrent_scrapes == 2

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

    @patch("pipeline.extract")
    @patch("pipeline.transform")
    @patch("pipeline.load")
    @patch("pipeline.compute_stats")
    def test_run_etl_process_events_fetch_failure(
        self, mock_compute_stats, mock_load, mock_transform, mock_extract
    ):
        """Test ETL process handles events API failure gracefully."""
        # Setup mocks

        # Mock extract result with events failure
        extract_result = ExtractResult(
            in_custody_ids={"1"},
            animals_by_id={"1": {"Internal-ID": "1", "ID": "A1", "Name": "Dog 1"}},
            events=[],  # Empty due to failure
            people=[{"person": "test"}],  # People succeeded
            existing_metadata={},
            memos_data={},
            scraped_map={},
            events_failed=True,  # Events failed
            people_failed=False,
        )
        mock_extract.return_value = extract_result

        # Mock transform result
        transform_result = TransformResult(
            dogs=[{"Internal-ID": "1"}], invalid_count=0, scraped_count=1, skipped_count=0
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
            people_fetch_failed=False,
        )

        config = EtlConfig(
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
        creds = {"api_key": "test_key", "username": "test", "password": "test"}
        stats = run_etl_process(config, creds)

        # Verify extract was called with correct 2-arg signature
        mock_extract.assert_called_once()
        (actual_creds, actual_cfg), _ = mock_extract.call_args
        assert actual_creds == creds
        assert isinstance(actual_cfg, ExtractConfig)
        assert actual_cfg.memos_mode == "api"
        assert actual_cfg.max_concurrent_scrapes == 2

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

    @patch("pipeline.extract")
    @patch("pipeline.transform")
    @patch("pipeline.load")
    @patch("pipeline.compute_stats")
    def test_run_etl_process_people_fetch_failure(
        self, mock_compute_stats, mock_load, mock_transform, mock_extract
    ):
        """Test ETL process handles people API failure gracefully."""
        # Setup mocks

        # Mock extract result with people failure
        extract_result = ExtractResult(
            in_custody_ids={"1"},
            animals_by_id={"1": {"Internal-ID": "1", "ID": "A1", "Name": "Dog 1"}},
            events=[{"event": "test"}],  # Events succeeded
            people=[],  # Empty due to failure
            existing_metadata={},
            memos_data={},
            scraped_map={},
            events_failed=False,
            people_failed=True,  # People failed
        )
        mock_extract.return_value = extract_result

        # Mock transform result
        transform_result = TransformResult(
            dogs=[{"Internal-ID": "1"}], invalid_count=0, scraped_count=1, skipped_count=0
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
            people_fetch_failed=True,
        )

        config = EtlConfig(
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
        creds = {"api_key": "test_key", "username": "test", "password": "test"}
        stats = run_etl_process(config, creds)

        # Verify extract was called with correct 2-arg signature
        mock_extract.assert_called_once()
        (actual_creds, actual_cfg), _ = mock_extract.call_args
        assert actual_creds == creds
        assert isinstance(actual_cfg, ExtractConfig)
        assert actual_cfg.memos_mode == "api"
        assert actual_cfg.max_concurrent_scrapes == 2

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

    @patch("pipeline.extract")
    @patch("pipeline.transform")
    @patch("pipeline.load")
    @patch("pipeline.compute_stats")
    def test_run_etl_process_dry_run_flag(
        self, mock_compute_stats, mock_load, mock_transform, mock_extract
    ):
        """Test that dry_run flag is properly passed through to load function."""
        # Setup mocks

        # Mock extract result
        extract_result = ExtractResult(
            in_custody_ids={"1"},
            animals_by_id={"1": {"Internal-ID": "1", "ID": "A1", "Name": "Dog 1"}},
            events=[],
            people=[],
            existing_metadata={},
            memos_data={},
            scraped_map={},
        )
        mock_extract.return_value = extract_result

        # Mock transform result
        transform_result = TransformResult(
            dogs=[{"Internal-ID": "1"}], invalid_count=0, scraped_count=1, skipped_count=0
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
        )

        # Run with dry_run=True
        config = EtlConfig(
            env_profile=EnvProfile.DEV,
            project_id="test-project",
            collection_name="dogs_test",
            secrets=SecretsConfig(mode=SecretsMode.ENV, project_id="test-project"),
            memos_mode="api",
            max_concurrent_scrapes=2,
            dry_run=True,
            animal_limit=None,
            skip_events_people=True,
        )
        creds = {"api_key": "test_key", "username": "test", "password": "test"}
        stats = run_etl_process(config, creds)

        # Verify load was called with dry_run=True
        mock_load.assert_called_once_with(transform_result, True)

    @patch("pipeline.extract")
    @patch("pipeline.transform")
    @patch("pipeline.load")
    @patch("pipeline.compute_stats")
    def test_run_etl_process_both_api_failures(
        self, mock_compute_stats, mock_load, mock_transform, mock_extract
    ):
        """Test ETL process handles both API failures gracefully."""
        # Setup mocks

        # Mock extract result with both failures
        extract_result = ExtractResult(
            in_custody_ids={"1"},
            animals_by_id={"1": {"Internal-ID": "1", "ID": "A1", "Name": "Dog 1"}},
            events=[],  # Empty due to failure
            people=[],  # Empty due to failure
            existing_metadata={},
            memos_data={},
            scraped_map={},
            events_failed=True,  # Events failed
            people_failed=True,  # People failed
        )
        mock_extract.return_value = extract_result

        # Mock transform result
        transform_result = TransformResult(
            dogs=[{"Internal-ID": "1"}], invalid_count=0, scraped_count=1, skipped_count=0
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
            people_fetch_failed=True,
        )

        config = EtlConfig(
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
        creds = {"api_key": "test_key", "username": "test", "password": "test"}
        stats = run_etl_process(config, creds)

        # Verify extract was called with correct 2-arg signature
        mock_extract.assert_called_once()
        (actual_creds, actual_cfg), _ = mock_extract.call_args
        assert actual_creds == creds
        assert isinstance(actual_cfg, ExtractConfig)
        assert actual_cfg.memos_mode == "api"
        assert actual_cfg.max_concurrent_scrapes == 2

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

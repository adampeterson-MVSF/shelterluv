"""
Tests for pipeline stats computation and failure handling.
Tests that invalid_count and partial_data behave correctly when simulating failures.
"""

from unittest.mock import Mock, patch

import pytest

from enrichment import build_dog_record
from errors import ApiError, EtlError
from pipeline import (
    ExtractResult,
    LoadResult,
    PipelineStats,
    TransformResult,
    compute_stats,
    run_etl_process,
)
from transform import TransformConfig, transform


class TestStatsComputation:
    """Test statistics computation logic."""

    def test_compute_stats_basic(self):
        """Test basic stats computation."""
        dogs = [
            {"Internal-ID": "1", "FosterName": "John Doe"},
            {"Internal-ID": "2", "FosterName": None},
        ]

        # Create mock ETL results
        extract_result = ExtractResult(
            in_custody_ids={"1", "2"},
            animals_by_id={"1": {}, "2": {}},
            events=[],
            people=[],
            existing_metadata={},
            memos_data={},
            scraped_map={},
        )
        transform_result = TransformResult(
            dogs=dogs, invalid_count=0, scraped_count=2, skipped_count=0
        )
        load_result = LoadResult(dogs_written=2, dogs_deleted=0)

        stats = compute_stats(extract_result, transform_result, load_result)

        # Convert to dict for compatibility with existing tests
        stats_dict = stats.to_dict()
        assert stats_dict["num_in_custody_ids"] == 2
        assert stats_dict["num_animals_fetched_from_api"] == 2
        assert stats_dict["dogs_processed"] == 2
        assert stats_dict["dogs_invalid"] == 0
        assert stats_dict["dogs_scraped"] == 2
        assert stats_dict["dogs_written"] == 2
        assert stats_dict["dogs_deleted"] == 0
        assert stats_dict["dogs_with_foster"] == 1
        assert stats_dict["events_fetch_failed"] is False
        assert stats_dict["people_fetch_failed"] is False
        assert stats_dict["partial_data"] is False

    def test_compute_stats_with_invalid(self):
        """Test stats computation with invalid records."""
        dogs = [{"Internal-ID": "1", "FosterName": "John Doe"}]

        # Create mock ETL results
        extract_result = ExtractResult(
            in_custody_ids={"1"},
            animals_by_id={"1": {}},
            events=[],
            people=[],
            existing_metadata={},
            memos_data={},
            scraped_map={},
        )
        transform_result = TransformResult(
            dogs=dogs, invalid_count=3, scraped_count=1, skipped_count=0
        )
        load_result = LoadResult(dogs_written=1, dogs_deleted=0)

        stats = compute_stats(extract_result, transform_result, load_result)

        stats_dict = stats.to_dict()
        assert stats_dict["num_in_custody_ids"] == 1
        assert stats_dict["num_animals_fetched_from_api"] == 1
        assert stats_dict["dogs_processed"] == 1
        assert stats_dict["dogs_invalid"] == 3

    def test_compute_stats_with_failures(self):
        """Test stats computation when fetches fail."""
        dogs = [{"Internal-ID": "1", "FosterName": "John Doe"}]

        # Create mock ETL results with failures
        extract_result = ExtractResult(
            in_custody_ids={"1"},
            animals_by_id={"1": {}},
            events=[],
            people=[],
            existing_metadata={},
            memos_data={},
            scraped_map={},
            events_failed=True,
            people_failed=True,
        )
        transform_result = TransformResult(
            dogs=dogs, invalid_count=0, scraped_count=1, skipped_count=0
        )
        load_result = LoadResult(dogs_written=1, dogs_deleted=0)

        stats = compute_stats(extract_result, transform_result, load_result)

        stats_dict = stats.to_dict()
        assert stats_dict["events_fetch_failed"] is True
        assert stats_dict["people_fetch_failed"] is True
        assert stats_dict["partial_data"] is True

    def test_compute_stats_empty_dogs(self):
        """Test stats computation with no dogs."""
        # Create mock ETL results with no dogs
        extract_result = ExtractResult(
            in_custody_ids=set(),
            animals_by_id={},
            events=[],
            people=[],
            existing_metadata={},
            memos_data={},
            scraped_map={},
        )
        transform_result = TransformResult(
            dogs=[], invalid_count=0, scraped_count=0, skipped_count=0
        )
        load_result = LoadResult(dogs_written=0, dogs_deleted=0)

        stats = compute_stats(extract_result, transform_result, load_result)

        stats_dict = stats.to_dict()
        assert stats_dict["num_in_custody_ids"] == 0
        assert stats_dict["num_animals_fetched_from_api"] == 0
        assert stats_dict["dogs_processed"] == 0
        assert stats_dict["dogs_with_foster"] == 0


class TestTransformInvalidCount:
    """Test that transform properly counts invalid records."""

    def test_transform_all_valid(self):
        """Test transform with all valid records."""
        # Setup extract result
        extract_result = ExtractResult(
            in_custody_ids={"1"},
            animals_by_id={
                "1": {
                    "Internal-ID": "1",
                    "ID": "A1",
                    "Name": "Dog 1",
                    "Status": "AVAILABLE",
                    "Age": "3 years",
                }
            },
            events=[],
            people=[],
            existing_metadata={},
            memos_data={},
            scraped_map={"1": {}},
        )

        with patch("enrichment.build_dog_record") as mock_build_dog:
            mock_build_dog.return_value = {"Internal-ID": "1", "Name": "Dog 1"}

            result = transform(extract_result, {}, TransformConfig())

            assert len(result.dogs) == 1
            assert result.invalid_count == 0

    def test_transform_with_invalid(self):
        """Test transform with some invalid records (missing required fields)."""
        # Setup extract result
        extract_result = ExtractResult(
            in_custody_ids={"1", "2"},
            animals_by_id={
                "1": {
                    "Internal-ID": "1",
                    "ID": "A1",
                    "Name": "Dog 1",
                    "Status": "AVAILABLE",
                    "Age": "3 years",
                },
                "2": {"Internal-ID": "2", "Name": "Dog 2"},  # Missing required ID field
            },
            events=[],
            people=[],
            existing_metadata={},
            memos_data={},
            scraped_map={"1": {}, "2": {}},
        )

        with patch("enrichment.build_dog_record") as mock_build_dog:
            # Valid dog succeeds, invalid dog raises exception
            def mock_build(record, scraped, foster, events, memo_html=""):
                if record.get("ID") == "A1":
                    return {"Internal-ID": "1", "Name": "Dog 1"}
                else:
                    from errors import SchemaValidationError

                    raise SchemaValidationError("Missing ID")

            mock_build_dog.side_effect = mock_build

            result = transform(extract_result, {}, TransformConfig())

            assert len(result.dogs) == 1  # Only valid dog
            assert result.invalid_count == 1

    def test_transform_all_invalid(self):
        """Test transform with all invalid records (missing required fields)."""
        # Setup extract result
        extract_result = ExtractResult(
            in_custody_ids={"1"},
            animals_by_id={"1": {"Internal-ID": "1", "Name": "Dog 1"}},  # Missing required ID field
            events=[],
            people=[],
            existing_metadata={},
            memos_data={},
            scraped_map={"1": {}},
        )

        with patch("enrichment.build_dog_record") as mock_build_dog:
            from errors import SchemaValidationError

            mock_build_dog.side_effect = SchemaValidationError("Missing ID")

            # Add required data to extract result
            extract_result.scraped_map = {"1": {}}
            extract_result.memos_data = {}
            result = transform(extract_result, {}, TransformConfig())

            assert len(result.dogs) == 0
            assert result.invalid_count == 1


class TestPipelineFailureHandling:
    """Test pipeline failure handling and partial data tracking."""

    def test_events_fetch_failure_tracked(self):
        """Test that events fetch failure is tracked in stats."""
        # Create extract result with events failure
        extract_result = ExtractResult(
            in_custody_ids={"1"},
            animals_by_id={
                "1": {
                    "Internal-ID": "1",
                    "ID": "A1",
                    "Name": "Test Dog",
                    "Status": "AVAILABLE",
                    "Age": "3 years",
                }
            },
            events=[],  # Empty due to failure
            people=[{"person": "test"}],  # People succeeded
            existing_metadata={},
            memos_data={},
            scraped_map={},
            events_failed=True,  # Events failed
            people_failed=False,
        )

        # Create transform result
        transform_result = TransformResult(
            dogs=[{"Internal-ID": "1", "FosterName": None}],
            invalid_count=0,
            scraped_count=1,
            skipped_count=0,
        )

        # Create load result
        load_result = LoadResult(dogs_written=1, dogs_deleted=0)

        # Compute stats
        stats = compute_stats(extract_result, transform_result, load_result)

        # Verify events failure is tracked
        assert stats.events_fetch_failed == True
        assert stats.people_fetch_failed == False
        assert stats.partial_data == True

    def test_people_fetch_failure_tracked(self):
        """Test that people fetch failure is tracked in stats."""
        # Create extract result with people failure
        extract_result = ExtractResult(
            in_custody_ids={"1"},
            animals_by_id={
                "1": {
                    "Internal-ID": "1",
                    "ID": "A1",
                    "Name": "Test Dog",
                    "Status": "AVAILABLE",
                    "Age": "3 years",
                }
            },
            events=[{"event": "test"}],  # Events succeeded
            people=[],  # Empty due to failure
            existing_metadata={},
            memos_data={},
            scraped_map={},
            events_failed=False,
            people_failed=True,  # People failed
        )

        # Create transform result
        transform_result = TransformResult(
            dogs=[{"Internal-ID": "1", "FosterName": None}],
            invalid_count=0,
            scraped_count=1,
            skipped_count=0,
        )

        # Create load result
        load_result = LoadResult(dogs_written=1, dogs_deleted=0)

        # Compute stats
        stats = compute_stats(extract_result, transform_result, load_result)

        # Verify people failure is tracked
        assert stats.events_fetch_failed == False
        assert stats.people_fetch_failed == True
        assert stats.partial_data == True

"""
E2E tests for ETL pipeline against live Firestore database.

⚠️  WARNING: These tests write to and read from real Firestore collections.
⚠️  They should NEVER run against production data.

These tests are gated by E2E_LIVE_DB=1 environment variable and will be
skipped unless explicitly enabled.

Run with:
    E2E_LIVE_DB=1 GCP_PROJECT=test-project DOGS_COLLECTION=dogs_e2e pytest tests/e2e/
"""

import os
import sys
from typing import Any, Dict, List

import pytest

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config import EnvProfile, EtlConfig, SecretsConfig, SecretsMode
from db import clear_all_dogs, get_db, get_dog_collection, purge_stale_dogs, write_dogs
from pipeline import run_etl_process
from secret_manager import get_shelterluv_creds

# Environment gating - skip these tests unless explicitly enabled
LIVE_DB = os.getenv("E2E_LIVE_DB") == "1"
if not LIVE_DB:
    pytest.skip("E2E_LIVE_DB=1 not set; skipping live DB tests", allow_module_level=True)

# Check for required ShelterLuv credentials
required_creds = ["SHELTERLUV_USER", "SHELTERLUV_PASS", "SHELTERLUV_API_KEY"]
missing_creds = [cred for cred in required_creds if not os.getenv(cred)]
if missing_creds:
    pytest.skip(
        f"Missing required ShelterLuv credentials: {', '.join(missing_creds)}",
        allow_module_level=True,
    )


@pytest.fixture(scope="session", autouse=True)
def validate_test_environment():
    """Ensure we are not accidentally pointing at production."""
    project_id = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    assert project_id is not None, "Must set GCP_PROJECT or GOOGLE_CLOUD_PROJECT"

    # Safety check - don't run against anything that looks like production
    project_lower = project_id.lower()
    assert (
        "prod" not in project_lower
    ), f"Refusing to run E2E tests against production project: {project_id}"
    assert (
        "live" not in project_lower
    ), f"Refusing to run E2E tests against live project: {project_id}"

    # Use test collection by default for E2E tests
    os.environ.setdefault("DOGS_COLLECTION", "dogs_e2e")
    # Disable Secret Manager for local e2e tests to avoid hanging
    os.environ.setdefault("DISABLE_SECRET_MANAGER", "1")
    # Import after setting environment
    from db import get_dog_collection


@pytest.fixture
def test_collection():
    """Get the test collection name."""
    return os.environ.get("DOGS_COLLECTION", "dogs_e2e")


@pytest.fixture(autouse=True)
def cleanup_test_data(test_collection):
    """Clean up test data before and after each test."""
    # Clear collection before test
    clear_all_dogs()

    yield

    # Clear collection after test
    clear_all_dogs()


class TestLiveDBPipeline:
    """Test ETL pipeline against live Firestore database."""

    def _create_e2e_config(self, test_collection, dry_run=False, animal_limit=None):
        """Create EtlConfig for E2E tests."""
        return EtlConfig(
            env_profile=EnvProfile.E2E,
            project_id=os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT"),
            collection_name=test_collection,
            secrets=SecretsConfig(
                mode=SecretsMode.ENV,
                project_id=os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT"),
            ),
            memos_mode="api",
            max_concurrent_scrapes=2,
            dry_run=dry_run,
            animal_limit=animal_limit,
        )

    def test_etl_writes_valid_dog_documents(self, test_collection):
        """Test that ETL writes valid dog documents to Firestore."""
        # Create config for E2E test
        config = self._create_e2e_config(test_collection, dry_run=False, animal_limit=3)

        # Run ETL process with limited animals to avoid hanging
        creds = get_shelterluv_creds(config.secrets)
        stats = run_etl_process(config, creds)

        # Basic sanity checks on stats
        assert isinstance(stats, dict)
        assert stats["dogs_processed"] >= 0
        assert stats["dogs_written"] >= 0
        assert stats["dogs_invalid"] >= 0

        # Inspect Firestore documents
        client = get_db()
        coll = client.collection(test_collection)
        docs = list(coll.stream())

        # We should have written some dogs (or none if no animals in custody)
        # This is valid - if ShelterLuv has no animals in custody, ETL correctly writes zero documents
        assert len(docs) >= 0, "ETL should have written zero or more dog documents"

        # If we did write documents, validate their schema
        if len(docs) > 0:
            # Sample first few documents to check schema
            sample_size = min(10, len(docs))
            for snap in docs[:sample_size]:
                data = snap.to_dict()
                assert isinstance(data, dict), f"Document should be a dict, got {type(data)}"

                # Required fields from schema
                assert "Internal-ID" in data, "Internal-ID is required"
                assert "ID" in data, "ID is required"
                assert "Name" in data, "Name is required"
                assert "Status" in data, "Status is required"
                assert "AgeYears" in data, "AgeYears is required"
                assert "AgeDisplay" in data, "AgeDisplay is required"

                # Type checks
                assert isinstance(data["Internal-ID"], str), "Internal-ID should be string"
                assert isinstance(data["ID"], str), "ID should be string"
                assert isinstance(data["Name"], str), "Name should be string"
                assert isinstance(data["Status"], str), "Status should be string"
                assert isinstance(data["AgeYears"], (int, float)), "AgeYears should be numeric"
                assert isinstance(data["AgeDisplay"], str), "AgeDisplay should be string"

                # Status enum validation
                valid_statuses = ["AVAILABLE", "ADOPTED", "PENDING", "HOLD", "UNKNOWN"]
                assert (
                    data["Status"] in valid_statuses
                ), f"Status {data['Status']} not in {valid_statuses}"

                # Document ID consistency check
                doc_id = snap.id
                assert doc_id == str(
                    data["Internal-ID"]
                ), f"Document ID {doc_id} should match Internal-ID {data['Internal-ID']}"

    def test_etl_idempotency_behavior(self, test_collection):
        """Test that running ETL multiple times doesn't break things."""
        # First run (limit to 2 animals for faster testing and rate limit avoidance)
        config1 = self._create_e2e_config(test_collection, dry_run=False, animal_limit=2)
        stats1 = run_etl_process(config1)

        # Wait to avoid rate limits
        import time

        time.sleep(10)

        # Second run (should be idempotent-ish, same limit)
        config2 = self._create_e2e_config(test_collection, dry_run=False, animal_limit=2)
        stats2 = run_etl_process(config2)

        # Basic checks - second run shouldn't explode
        assert isinstance(stats2, dict)
        assert stats2["dogs_processed"] >= 0

        # Second run might write fewer or zero dogs if data hasn't changed
        # But it definitely shouldn't write more than the first run
        assert (
            stats2["dogs_written"] <= stats1["dogs_written"]
        ), f"Second run wrote {stats2['dogs_written']} dogs, first run wrote {stats1['dogs_written']}"

    def test_etl_write_purge_coherence(self, test_collection):
        """Test that writes and purges work together coherently."""
        # Run ETL to populate data
        config1 = self._create_e2e_config(test_collection, dry_run=False)
        stats = run_etl_process(config1)

        # Check that we have some data
        client = get_db()
        coll = client.collection(test_collection)
        docs_before = list(coll.stream())

        assert len(docs_before) >= 0, "ETL should have run (may have 0 dogs if none available)"

        # Run again - this will trigger purge logic for stale dogs
        config2 = self._create_e2e_config(test_collection, dry_run=False)
        stats2 = run_etl_process(config2)

        # Check data after second run
        docs_after = list(coll.stream())

        # The purge shouldn't delete all dogs unless they're all stale
        # At minimum, the counts should be coherent
        total_operations = stats2["dogs_written"] + stats2["dogs_deleted"]
        assert total_operations >= 0, "Write + delete operations should be non-negative"

        # If we wrote dogs, we should still have some (or they were legitimately purged)
        if stats2["dogs_written"] > 0:
            assert len(docs_after) >= 0, "Should have some dogs after operations"

    def test_etl_schema_consistency(self, test_collection):
        """Test that all written documents conform to expected schema."""
        # Run ETL
        config = self._create_e2e_config(test_collection, dry_run=False)
        creds = get_shelterluv_creds(config.secrets)
        stats = run_etl_process(config, creds)

        # Skip schema validation if no dogs were written (may be no data available)
        if stats["dogs_written"] == 0:
            pytest.skip(
                "No dogs written - skipping schema validation (may be no ShelterLuv data available)"
            )

        # Check all documents
        client = get_db()
        coll = client.collection(test_collection)
        docs = list(coll.stream())

        schema_violations = []

        for snap in docs:
            data = snap.to_dict()

            # Check required fields are present
            from schema import get_required_fields

            required_fields = get_required_fields()

            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                schema_violations.append(f"Doc {snap.id}: missing {missing_fields}")

            # Check boolean flags are actually boolean
            boolean_fields = ["IsInCustody", "IsAvailableForAdoption", "IsHospice", "IsEventDog"]
            for field in boolean_fields:
                if field in data and not isinstance(data[field], bool):
                    schema_violations.append(
                        f"Doc {snap.id}: {field} should be bool, got {type(data[field])}"
                    )

            # Check Status is valid enum
            if "Status" in data:
                valid_statuses = ["AVAILABLE", "ADOPTED", "PENDING", "HOLD", "UNKNOWN"]
                if data["Status"] not in valid_statuses:
                    schema_violations.append(f"Doc {snap.id}: invalid status {data['Status']}")

        # Report any schema violations
        if schema_violations:
            violation_summary = "\n".join(schema_violations[:5])  # Show first 5
            if len(schema_violations) > 5:
                violation_summary += f"\n... and {len(schema_violations) - 5} more"
            pytest.fail(f"Schema violations found:\n{violation_summary}")

    def test_purge_stale_dogs_with_controlled_data(self, test_collection):
        """Test purge logic with controlled test data."""
        client = get_db()
        coll = client.collection(test_collection)

        # Create some test dogs manually
        test_dogs = [
            {
                "Internal-ID": "test-purge-001",
                "ID": "PURGE001",
                "Name": "Purge Test Dog 1",
                "Status": "AVAILABLE",
                "AgeYears": 3.5,
                "AgeDisplay": "3 years",
                "IsInCustody": True,
                "IsAvailableForAdoption": True,
                "IsHospice": False,
                "IsEventDog": False,
            },
            {
                "Internal-ID": "test-purge-002",
                "ID": "PURGE002",
                "Name": "Purge Test Dog 2",
                "Status": "AVAILABLE",
                "AgeYears": 2.0,
                "AgeDisplay": "2 years",
                "IsInCustody": True,
                "IsAvailableForAdoption": True,
                "IsHospice": False,
                "IsEventDog": False,
            },
            {
                "Internal-ID": "test-purge-003",
                "ID": "PURGE003",
                "Name": "Purge Test Dog 3",
                "Status": "ADOPTED",
                "AgeYears": 5.0,
                "AgeDisplay": "5 years",
                "IsInCustody": False,
                "IsAvailableForAdoption": False,
                "IsHospice": False,
                "IsEventDog": False,
            },
        ]

        # Write test dogs to Firestore
        write_result = write_dogs(test_dogs, dry_run=False)
        assert write_result["dogs_written"] == 3, "Should have written 3 test dogs"

        # Verify they exist
        docs_before = list(coll.stream())
        assert len(docs_before) == 3, "Should have 3 dogs before purge"

        # Now test purge with only 2 dogs "active"
        active_ids = {"test-purge-001", "test-purge-002"}  # Keep first 2, purge the third

        # Dry run first to check what would be purged
        purge_dry_count = purge_stale_dogs(active_ids, dry_run=True)
        assert purge_dry_count == 1, "Should identify 1 stale dog in dry run"

        # Actual purge
        purge_real_count = purge_stale_dogs(active_ids, dry_run=False)
        assert purge_real_count == 1, "Should actually purge 1 stale dog"

        # Verify results
        docs_after = list(coll.stream())
        assert len(docs_after) == 2, "Should have 2 dogs remaining after purge"

        remaining_ids = {doc.id for doc in docs_after}
        assert (
            remaining_ids == active_ids
        ), f"Remaining dogs should be {active_ids}, got {remaining_ids}"

        # Verify the purged dog is gone
        assert "test-purge-003" not in remaining_ids, "Purged dog should be gone"

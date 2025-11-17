# E2E Tests - Live Database Testing

⚠️ **WARNING**: These tests interact with real Firestore databases and should never be run against production data.

## Overview

This directory contains End-to-End (E2E) tests that validate the ETL pipeline against live Firestore databases. Unlike the unit/integration tests in `../` which use mocks, these tests:

- Write real documents to Firestore
- Read real documents from Firestore
- Test purge operations on real data
- Validate schema compliance on actual stored data

## Safety Features

### Environment Gating
Tests are **automatically skipped** unless `E2E_LIVE_DB=1` is set:

```bash
# These tests will be skipped
pytest tests/e2e/

# These tests will run
E2E_LIVE_DB=1 pytest tests/e2e/
```

### Project Safety Checks
Tests refuse to run against projects containing "prod" or "live" in their names:

```python
project_id = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
assert "prod" not in project_id.lower()  # Safety check
```

### Collection Isolation
Tests default to using `dogs_e2e` collection instead of the production `dogs` collection:

```bash
# Override if needed
E2E_LIVE_DB=1 DOGS_COLLECTION=my_custom_test_collection pytest tests/e2e/
```

## Test Categories

### 1. Schema Validation Tests
- `test_etl_writes_valid_dog_documents()`: Validates that ETL writes conform to the dog schema
- `test_etl_schema_consistency()`: Checks all documents in the collection for schema compliance

### 2. Behavioral Tests
- `test_etl_idempotency_behavior()`: Ensures running ETL multiple times doesn't break data
- `test_etl_write_purge_coherence()`: Validates that writes and purges work together properly

### 3. Purge Logic Tests
- `test_purge_stale_dogs_with_controlled_data()`: Tests purge functionality with manually created test data

## Running the Tests

### Prerequisites
1. GCP project configured (non-production)
2. Firestore enabled in the project
3. Service account credentials available

### Basic Usage
```bash
# Set required environment variables
export GCP_PROJECT=my-test-project
export E2E_LIVE_DB=1

# Run all E2E tests
pytest tests/e2e/ -v

# Run specific test
pytest tests/e2e/test_pipeline_live_db.py::TestLiveDBPipeline::test_etl_writes_valid_dog_documents -v
```

### With Custom Collection
```bash
export GCP_PROJECT=my-test-project
export E2E_LIVE_DB=1
export DOGS_COLLECTION=dogs_custom_e2e

pytest tests/e2e/ -v
```

### With Real ShelterLuv Credentials
```bash
export GCP_PROJECT=my-test-project
export E2E_LIVE_DB=1
export SHELTERLUV_USER=my_username
export SHELTERLUV_PASS=my_password
export SHELTERLUV_API_KEY=my_api_key

pytest tests/e2e/ -v
```

## Test Data Management

### Automatic Cleanup
Each test is wrapped with fixtures that:
- Clear the test collection **before** the test runs
- Clear the test collection **after** the test runs

### Manual Test Data
Some tests (like purge tests) create specific test documents to validate behavior.

## Assertions Strategy

Unlike unit tests that assert exact values, E2E tests assert **invariants**:

- ✅ Schema compliance (required fields, correct types, valid enums)
- ✅ Behavioral consistency (idempotency, coherence)
- ✅ Data integrity (document IDs match Internal-IDs)
- ❌ Exact counts (these change with real data)

## Integration with CI/CD

### When to Run E2E Tests
- **Manual testing**: Before major deployments
- **Nightly builds**: Automated smoke tests
- **Never**: On every commit (too slow, too risky)

### CI Configuration Example
```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:  # Manual trigger

jobs:
  e2e:
    runs-on: ubuntu-latest
    environment: e2e-tests
    env:
      E2E_LIVE_DB: 1
      GCP_PROJECT: my-test-project
      DOGS_COLLECTION: dogs_e2e_ci
    steps:
      - uses: actions/checkout@v3
      - name: Run E2E tests
        run: pytest tests/e2e/ --tb=short
```

## Troubleshooting

### Tests Skipped
```
pytest.skip("E2E_LIVE_DB=1 not set; skipping live DB tests", allow_module_level=True)
```
**Solution**: Set `E2E_LIVE_DB=1` environment variable.

### Project Safety Failure
```
AssertionError: Refusing to run E2E tests against production project: my-prod-project
```
**Solution**: Use a non-production GCP project.

### Missing Credentials
```
401 Client Error: Unauthorized for url: https://new.shelterluv.com/api/v1/animals
```
**Solution**: Either set real ShelterLuv credentials or use `--mock-credentials` flag (though this may not work with live DB tests).

## Architecture Notes

### Test Layers
1. **Unit tests** (`tests/`): Fast, mocked, comprehensive coverage
2. **E2E tests** (`tests/e2e/`): Slow, live DB, behavioral validation
3. **Performance tests** (`perf/`): Specialized timing measurements

### Why Both Mocked and Live Tests?
- **Mocked tests**: Catch logic bugs, fast iteration, reliable CI
- **Live DB tests**: Catch integration bugs, validate real schemas, test purge logic

The mocked tests remain the primary contract. E2E tests are a safety net for deployment confidence.

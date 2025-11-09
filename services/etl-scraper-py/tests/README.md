# ETL Service Tests

This directory contains unit and integration tests for the ETL scraper service.

## Credential Setup

Tests require ShelterLuv credentials to run properly. Credentials come from multiple sources (checked in order of priority):

### 1. Google Cloud Secret Manager (Production/Recommended)
- `SHELTERLUV_USER` - ShelterLuv username
- `SHELTERLUV_PASS` - ShelterLuv password
- `SHELTERLUV_API_KEY` - ShelterLuv API key

### 2. Environment Variables (Development)
Set these in your shell or in a `.env.local` file:

```bash
SHELTERLUV_USER=your_username
SHELTERLUV_PASS=your_password
SHELTERLUV_API_KEY=your_api_key
```

### 3. Local .env Files
Create `services/etl-scraper-py/.env.local` with:

```bash
# ShelterLuv API Credentials
SHELTERLUV_USER=your_username
SHELTERLUV_PASS=your_password
SHELTERLUV_API_KEY=your_api_key
```

## Quick Credential Verification

Run the credential checker:
```bash
cd services/etl-scraper-py
python check_credentials.py
```

## Test Categories

### Unit Tests
- **test_schema_and_flags.py**: Schema validation and data normalization
- **test_enrichment.py**: Foster mapping and structured notes parsing
- **test_errors.py**: Error hierarchy and exception handling
- **test_secret_manager.py**: Credential management and caching

### Integration Tests
- **test_api_client.py**: ShelterLuv API client functionality
- **test_db.py**: Firestore database operations
- **test_pipeline.py**: ETL pipeline orchestration
- **test_integration.py**: Full ETL pipeline integration

### End-to-End Tests
- **e2e/**: Live database testing (see e2e/README.md)

## Running Tests

### All Tests
```bash
cd services/etl-scraper-py
python -m pytest tests/ -v
```

### Specific Test File
```bash
python -m pytest tests/test_schema_and_flags.py -v
```

### With Coverage
```bash
python -m pytest tests/ --cov=. --cov-report=html
```

## Common Test Failures

### Import Errors
```
ImportError: cannot import name 'transform_enrich' from 'pipeline'
```
**Solution**: The tests have been updated to use the correct `transform` function from the `transform` module.

### Credential Errors
```
EtlError: ShelterLuv credentials not found in Secret Manager or environment variables
```
**Solution**: Set up credentials as described in the "Credential Setup" section above.

### Firestore Connection Issues
```
Firestore connection failed: Cannot read properties of undefined (reading 'exists')
```
**Solution**: Ensure Google Cloud credentials are properly configured for your environment.

## Test Architecture

### Mock Strategy
- **Firebase/Firestore**: Fully mocked to avoid real database calls
- **ShelterLuv API**: Mocked HTTP responses for API client tests
- **File system**: Mocked for scraper tests

### Environment Variables
Tests automatically load from `.env.local` files, so you don't need to export variables manually for local development.

### Test Data
- **Fixtures**: Predefined test data structures
- **Mock responses**: Simulated API responses
- **Generated data**: Random but valid test records

## Contributing

When adding new tests:
1. Include clear docstrings explaining what the test validates
2. Mock external dependencies (APIs, databases, file system)
3. Use descriptive test names and assertions
4. Add credential setup comments if the test requires real credentials

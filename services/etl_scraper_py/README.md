# ETL Scraper Service

ShelterLuv data extraction, transformation, and loading pipeline for the Muttville adoption platform.

## Architecture

### Core ETL Pipeline

The ETL pipeline follows a clean architecture with clear separation of concerns:

```
extract.py     - Data extraction from ShelterLuv (API + scraping)
transform.py   - Data processing and normalization
load.py        - Data persistence to Firestore
pipeline.py    - Orchestration and statistics
```

### Package Structure

```
etl_scraper_py/
├── api/                    # ShelterLuv API clients
│   ├── __init__.py
│   ├── api_client_animals.py
│   ├── api_client_events.py
│   ├── api_client_memos.py
│   ├── api_client_people.py
│   └── api_client_base.py
├── scraper/                # Web scraping utilities
│   ├── __init__.py
│   ├── in_custody_ids.py
│   ├── session.py
│   ├── navigation.py
│   └── parsers.py          # Uses Animal Record Summary pages
├── tools/                  # Utility scripts and tools
├── config.py               # Configuration management
├── errors.py               # Custom exception classes
├── common.py               # Shared utilities
├── schema.py               # Data validation schemas
├── db.py                   # Database operations
├── enrichment.py           # Data enrichment logic
├── flags.py                # Feature flags
├── foster_mapping.py       # Foster relationship mapping
├── normalization.py        # Data normalization
├── secret_manager.py       # Credential management
├── main.py                 # Cloud Functions entry point
├── run_etl_local.py        # Local development runner
├── pipeline.py             # ETL orchestration
├── extract.py              # Extract phase
├── transform.py            # Transform phase
├── load.py                 # Load phase
└── tests/                  # Test suite
```

## Configuration

The ETL pipeline uses unified configuration from `common/config.json`:

- **Environment Profiles**: `python_env_profiles` maps profile names (`dev`, `staging`, `e2e`, `demo`, `prod`) to GCP project IDs
- **Safe Profiles**: `safe_profiles` lists profiles allowed for development operations
- **Environment Variables**: `env_profiles.etl` defines required/optional env vars

The `config.py` module loads this configuration via `config_loader.py`. Never hardcode project IDs or profile lists.

### Safety Invariants

**Safety is defined over project IDs, not profile names.** Any changes to `common/config.json` must keep JS and Python safety maps equivalent:

- `config_loader.get_project_safety()` returns `{project_id → {env_profile, is_safe}}`
- `common/configData.getNormalizedProfileMap()` returns `{profile → {gcp_project, is_safe}}`
- Both must produce consistent safety decisions for the same project ID
- Cross-language tests in `tests/test_cross_language_safety.py` enforce this equivalence

Project ID overrides in ETL configuration are validated against the safety map - they cannot bypass profile-based safety rules.

## Usage

### Local Development

Run the full ETL pipeline locally:

```bash
# Full ETL run (uses GCP_PROJECT from env, validates against config.json)
# Scrapes from animal record summary pages for comprehensive data
python run_etl_local.py

# Test with limited data
python run_etl_local.py --limit 5

# Dry run (no database writes)
python run_etl_local.py --dry-run

# Include events and people fetching (slower, more complete data)
SKIP_EVENTS_PEOPLE=false python run_etl_local.py

# Include memo processing (slower)
python run_etl_local.py --memos-mode api
```

**Scraping Method**: The pipeline now uses the Animal Record Summary page (`/animals/documents/animal-record-summary?animals={internal_id}`) which provides comprehensive animal data in a single, well-structured document. This approach is more reliable and efficient than navigating multiple profile tabs.

**Data Extracted**:
- **Basic Info**: Species, Breed, Color, Pattern, Distinguishing Marks, Age, DOB
- **Medical**: Vaccination history, treatments, diagnostic tests, microchip info
- **Behavioral**: Compatibility ratings, energy levels, special attributes
- **Photos**: Direct image URLs from ShelterLuv
- **Complete History**: Intake/outcome records, status changes, locations

**Environment Setup:**
- Set `GCP_PROJECT` to a safe project from `common/config.json` (e.g., `dev-muttville`, `staging-muttville`)
- Set `SHELTERLUV_USER`, `SHELTERLUV_PASS`, `SHELTERLUV_API_KEY` for API access
- Set `DISABLE_SECRET_MANAGER=1` to use env vars instead of GCP Secret Manager

### Production Deployment

The ETL pipeline runs as a Google Cloud Function triggered by HTTP requests:

```bash
# Deploy to GCP
gcloud functions deploy run-shelterluv-etl \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated
```

### API Package

Unified access to ShelterLuv API endpoints:

```python
from api import (
    get_animals_by_ids,
    get_animal_events,
    get_people,
    get_animal_memos
)

# Get animal data
animals = get_animals_by_ids(internal_ids, api_key)

# Get related data
events = get_animal_events(api_key)
people = get_people(api_key)
```

## Development Tools

### Debug Scripts (`debug/`)

Diagnostic tools for troubleshooting ETL issues:

- `debug_etl_minimal.py` - Minimal ETL run for testing
- `debug_etl_simple.py` - Simplified ETL pipeline
- `debug_api.py` - API connectivity testing
- `debug_in_custody_scraping.py` - In-custody ID scraping diagnostics

### Utility Tools (`tools/`)

Development and operational utilities:

- `check_credentials.py` - Validate API credentials
- `find_animal_by_id.py` - Lookup specific animals
- `get_specific_animal.py` - Fetch individual animal details
- `compare_etl_vs_ui.py` - Compare ETL data with UI
- `validate_scraped_data.py` - Data validation tools

## Configuration

### Environment Variables

Required for all operations:

```bash
# Firebase
FIREBASE_PROJECT_ID=your-project-id

# ShelterLuv API
SHELTERLUV_USER=your-username
SHELTERLUV_PASS=your-password
SHELTERLUV_API_KEY=your-api-key

# Optional
ENV_PROFILE=dev|staging|e2e|demo|prod
SKIP_EVENTS_PEOPLE=false  # Override default (true) to fetch events/people data
DISABLE_API_RATE_LIMITING=1  # For testing
```

### Configuration Management

ETL behavior is controlled through:

- `config.py` - Runtime configuration and environment profiles
- `flags.py` - Feature flags for enabling/disabling features
- `common.py` - Shared constants and utilities

## Testing

### Unit Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_pipeline_transform.py
pytest tests/test_pipeline_orchestration.py

# Run with coverage
pytest --cov=.

# Run integration tests
pytest tests/test_integration.py
```

**Test Fixtures**: Tests use shared fixtures from `tests/conftest.py`, including a `parser` fixture for memo parsing tests and standard configuration fixtures. See `tests/README.md` for details.

### Performance Testing

Measure ETL pipeline performance with configurable scenarios:

```bash
# Basic performance test (dry-run by default)
python perf/pipeline_performance_test.py --dogs 10

# With memo processing
python perf/pipeline_performance_test.py --dogs 20 --memos-mode api

# Quick development test
python perf/pipeline_performance_test.py --dogs 3 --iterations 1
```

**Performance Characteristics**:
- **Sequential scraping bottleneck**: ~44-46s per dog due to web scraping
- **API calls**: Efficient concurrent processing (events/people fetching adds ~30-60s when enabled)
- **Database**: Fast batch operations
- **Default behavior**: Events/people fetching skipped by default for faster execution
- **Scaling**: Parallel scraping needed for >10 dogs

**Optimization Priority**:
1. **High Impact**: API-first enrichment (eliminate scraping)
2. **Medium Impact**: Parallel scraping with asyncio
3. **Low Impact**: Incremental updates and caching

## Data Flow

1. **Extract**: Scrape in-custody animal IDs from ShelterLuv UI, then fetch detailed data via API
2. **Transform**: Normalize data, enrich with memos/events/people, validate against schema
3. **Load**: Write to Firestore with incremental updates and change tracking

### Key Data Structures

- `ExtractResult`: Raw data from ShelterLuv
- `TransformResult`: Processed and enriched data
- `LoadResult`: Persistence results and statistics
- `PipelineStats`: Comprehensive pipeline metrics

## Error Handling

Custom exception hierarchy in `errors.py`:

- `EtlError`: Base ETL exception
- `ApiError`: ShelterLuv API failures
- `ScraperError`: Web scraping failures
- `SchemaValidationError`: Data validation failures

All errors include structured context for debugging and monitoring.

## Monitoring

### Logging

Structured logging with context:

```python
import logging
logger = logging.getLogger(__name__)
logger.info("Processing %d animals", len(animals))
```

### Metrics

Pipeline statistics tracked in `PipelineStats`:

- Animal counts by phase
- API call success/failure rates
- Performance timing data
- Data quality metrics

## Development

### Adding New API Endpoints

1. Create new client in `api/api_client_*.py`
2. Add to `api/__init__.py` exports
3. Update type hints and documentation
4. Add tests in `tests/test_api_client.py`

### Modifying ETL Pipeline

1. Update appropriate phase (extract/transform/load)
2. Update `PipelineStats` if new metrics needed
3. Update tests
4. Update documentation

### Adding Debug Tools

1. Create script in `debug/` directory
2. Follow existing patterns for imports and error handling
3. Add usage documentation in docstring

## Security

- Credentials managed through `secret_manager.py`
- Environment-based access controls
- Safe defaults prevent production data modification
- Audit logging for all operations

## Performance

- Concurrent API calls with configurable limits
- Rate limiting to respect ShelterLuv API
- Incremental updates to minimize processing
- Memory-efficient streaming for large datasets

## Troubleshooting

### Common Issues

1. **API Rate Limiting**: Check `DISABLE_API_RATE_LIMITING` or reduce concurrency
2. **Scraping Failures**: Use debug scripts to isolate scraping issues
3. **Schema Validation**: Run `debug_etl_minimal.py` to test data processing
4. **Firebase Issues**: Check project configuration and permissions

### Debug Workflow

```bash
# 1. Test API connectivity
python debug/debug_api.py

# 2. Test scraping
python debug/debug_in_custody_scraping.py

# 3. Test minimal ETL
python debug/debug_etl_minimal.py

# 4. Full pipeline with limited data
python run_etl_local.py --limit 3
```
# ETL Pipeline Performance Testing

Measures ETL pipeline performance with concurrent scraping and API integration.

## Supported Commands

```bash
# Basic performance test (recommended)
cd services/etl-scraper-py
python perf/pipeline_performance_test.py --dogs 10

# With memo extraction
python perf/pipeline_performance_test.py --dogs 20 --memos-mode api

# Quick test for development
python perf/pipeline_performance_test.py --dogs 3 --iterations 1
```

## What It Measures

- Total execution time for ETL pipeline
- Stage-by-stage timing (extract/transform/load)
- Memory usage (if psutil available)
- Processing statistics (dogs processed/written/deleted)
- Per-dog performance metrics

## Safety

- **Dry-run by default** - no actual Firestore writes
- **Environment guards** prevent production database access
- Requires `GOOGLE_CLOUD_PROJECT` set to safe project (dev-muttville, staging-muttville, muttville-demo)

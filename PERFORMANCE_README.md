# Performance Testing

Performance tests call live ShelterLuv endpoints and Firestore. Run only against non-production projects.

**⚠️ SAFETY**: All perf tests use `common/devScriptSafety.js` (Node) or `config.py` `SafetyPolicy` (Python). Projects must be in `common/config.json` `safe_profiles`. **NEVER** run against production (`muttville-prod`, `muttville-production`).

**Canonical Entry Points:**
- **Orchestrator**: `scripts/run_performance_tests.js` - Runs both suites
- **ETL**: `services/etl_scraper_py/perf/pipeline_performance_test.py` - ETL pipeline metrics
- **Webapp**: `services/webapp-react/perf/performance_test.js` - Frontend render/load metrics

**No second config system**: Perf tests use the same config as main ETL/webapp (`common/config.json`, `config.py`, `SafetyPolicy`).

## Prerequisites Checklist

- [ ] Select an approved staging project from `common/config.json` `safe_profiles` list (`dev`, `staging`, `e2e`, or `demo`) and confirm it contains representative dog data.
- [ ] Export required environment variables:
  - `FIREBASE_PROJECT_ID=staging-muttville` (or another safe project from `common/config.json` `safe_profiles`)
  - `GCP_PROJECT=staging-muttville` (must match `FIREBASE_PROJECT_ID` and be in `safe_profiles`)
  - `SHELTERLUV_USER`, `SHELTERLUV_PASS`, `SHELTERLUV_API_KEY` when exercising the real API.
- [ ] Sign in with `gcloud auth application-default login` so Firestore and Secret Manager clients can authenticate.
- [ ] Regenerate schema artifacts with `npm run schema:gen` to keep ETL/webapp contracts in sync before measuring performance.

## One-Command Orchestrator

Run both performance suites in one shot:

```bash
node scripts/run_performance_tests.js
```

The orchestrator shells out to:

- `services/etl_scraper_py/perf/pipeline_performance_test.py`
- `services/webapp-react/perf/performance_test.js`

It writes JSON artifacts into `artifacts/` and prints a consolidated summary.

## Performance Thresholds

### Contractually Important Metrics (CI-Enforced)

These metrics are contractually enforced in CI. Failures block merges and require immediate attention.

| Metric | JSON Key | Source File | Threshold | How to Fix |
|--------|----------|-------------|-----------|------------|
| ETL Total Time | `total_time` | `services/etl_scraper_py/perf/pipeline_performance_test.py` | < 60s for 10 dogs | Optimize concurrent scraping in `services/etl_scraper_py/scraper/` |
| ETL Memory Peak | `memory_peak` | `services/etl_scraper_py/perf/pipeline_performance_test.py` | < 300MB | Reduce concurrent workers in `services/etl_scraper_py/transform.py` |
| Webapp Page Load | `homePageLoad.average` | `services/webapp-react/perf/performance_test.js` | < 2000ms | Optimize dog data fetching in `services/webapp-react/src/hooks/useDogs.js` |

### Nice-to-Have Metrics (Monitoring Only)

These metrics are tracked for awareness but don't block CI. Investigate if they degrade significantly.

| Metric | JSON Key | Source File | Threshold | How to Fix |
|--------|----------|-------------|-----------|------------|
| ETL Scrape Time | `scrape_transform_time` | `services/etl_scraper_py/perf/pipeline_performance_test.py` | < 30s for 10 dogs | Add retry logic and timeouts in `services/etl_scraper_py/scraper/session.py` |
| Webapp Filtering | `filtering.measurements[].average` | `services/webapp-react/perf/performance_test.js` | < 500ms | Add indexes to Firestore queries in `services/webapp-react/src/repositories/dogRepository.js` |
| Webapp Search | `search.measurements[].average` | `services/webapp-react/perf/performance_test.js` | < 300ms | Implement client-side search optimization in `services/webapp-react/src/hooks/useDogs.js` |

**Note**: Keep this table authoritative with CI expectations—update both together whenever a threshold changes.

## How to Interpret Failures

### CI Failure Scenarios

1. **ETL Total Time > 60s**: Pipeline is too slow for production. Check:
   - Network latency to ShelterLuv API
   - Concurrent worker count in `transform.py`
   - Firestore write batch sizes
   - **Action**: Optimize bottlenecks or increase threshold if justified

2. **ETL Memory Peak > 300MB**: Risk of OOM in production. Check:
   - Number of concurrent workers
   - Large data structures in memory
   - **Action**: Reduce concurrency or optimize memory usage

3. **Webapp Page Load > 2000ms**: Poor user experience. Check:
   - Firestore query performance (add indexes)
   - Network conditions
   - **Action**: Optimize queries, add indexes, or lazy load routes

### Non-Blocking Degradations

If nice-to-have metrics degrade but don't exceed thresholds:
- Monitor trends over multiple runs
- File a non-blocking issue if degradation is consistent
- Investigate during next performance sprint

### Test Environment Issues

If tests fail due to environment (not code):
- Verify project is in `safe_profiles` list
- Check `FIREBASE_PROJECT_ID` and `GCP_PROJECT` are set correctly
- Ensure `gcloud auth application-default login` is complete
- Re-run tests; if still failing, check Firestore connectivity

## ETL Performance Testing

### Checklist

1. `cd services/etl_scraper_py`
2. `python3 perf/pipeline_performance_test.py --dogs 10`
   - Append `--write` to hit Firestore for real writes; default is dry-run.
3. Save stdout to `perf/etl_run.json`.
4. Confirm:
   - `total_time < 60`
   - `memory_peak < 300000000`
   - `dogs_processed == --dogs`
5. File a regression issue if any metric fails or output `success` is `false`.

### JSON Shape

```json
{
  "total_time": 45.67,
  "extract_animals_time": 2.34,
  "extract_events_time": 8.91,
  "extract_people_time": 1.23,
  "transform_mappings_time": 0.56,
  "scrape_transform_time": 25.43,
  "load_time": 7.20,
  "memory_peak": 234567890,
  "memory_current": 123456789,
  "dogs_processed": 10,
  "dogs_written": 10,
  "dogs_deleted": 0,
  "success": true
}
```

### Compare Runs Quickly

```bash
python3 perf/pipeline_performance_test.py --dogs 10 > perf/run1.json
python3 perf/pipeline_performance_test.py --dogs 10 > perf/run2.json
jq '.total_time' perf/run1.json perf/run2.json
```

## Webapp Performance Testing

### Checklist

1. `cd services/webapp-react`
2. Start dev server: `npm run dev` (runs on port 5173 by default)
3. Run `node perf/performance_test.js --iterations 3 --port 5173`
4. Inspect `perf/performance_results_*.json` and verify:
   - Home Page Load `average < 2000`
   - Filtering scenarios `average < 500`
   - Search scenarios `average < 300`
5. Attach the JSON output to any regression report.

### Result Shape

```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "config": {
    "port": 5173,
    "scenarios": ["homePageLoad", "filtering", "search"]
  },
  "results": {
    "homePageLoad": {
      "name": "Home Page Load Performance",
      "description": "Measure time to load home page and display dog data",
      "measurements": [
        {
          "iteration": 1,
          "duration": 1234,
          "success": true,
          "loadTime": 1234,
          "dogCount": 8,
          "authStatus": true
        }
      ]
    },
    "filtering": {
      "name": "Filtering Performance",
      "description": "Test filtering operations with various combinations",
      "measurements": [
        {
          "scenario": "No filters",
          "measurements": [
            {
              "iteration": 1,
              "duration": 45,
              "success": true,
              "filterTime": 45,
              "visibleDogs": 10,
              "activeFilters": 0
            }
          ],
          "average": 45.2,
          "successRate": 100
        }
      ]
    }
  }
}
```

### Compare Runs Quickly

```bash
ls perf/performance_results_*.json
jq '.results.homePageLoad.measurements[0].duration' perf/performance_results_*.json
```

## Running Both Together

```bash
node scripts/run_performance_tests.js
```

This runs both ETL and webapp performance tests, coordinating the execution and writing JSON artifacts for CI consumption.


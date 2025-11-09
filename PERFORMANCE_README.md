# Performance Testing

**⚠️ SAFETY FIRST**: Performance scripts hit real ShelterLuv APIs and Firebase. Use only with staging/test projects.

Set environment variables:
- `FIREBASE_ENV=staging` (see `common/firebaseSafetyConfig.js` for allowed projects)
- `GOOGLE_CLOUD_PROJECT=muttville-staging` (see `services/etl-scraper-py/common.py` for project mapping)

**What "Good Enough" Means:**
- **ETL**: Process 10 dogs in < 60 seconds (6 seconds/dog) with < 300MB memory
- **Webapp**: Page loads in < 2 seconds, bundle < 2MB, Lighthouse score ≥ 90

## ETL Performance Testing

### Run Performance Test
```bash
cd services/etl-scraper-py
python perf/pipeline_performance_test.py --dogs 10
```

**Note**: Runs in dry-run mode by default (no actual Firestore writes). Use `--write` for full end-to-end testing.

### Expected JSON Output
The script outputs a single JSON object to stdout:

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

### Compare Runs
```bash
# Run twice and compare manually
python perf/pipeline_performance_test.py --dogs 10 > run1.json
python perf/pipeline_performance_test.py --dogs 10 > run2.json

# Compare total_time field
jq '.total_time' run1.json run2.json
```

### Target Performance
- `total_time`: < 60 seconds for 10 dogs (6 seconds per dog)
- `memory_peak`: < 300MB
- `dogs_processed`: Should match `--dogs` parameter

## Webapp Performance Testing

### Run Performance Test
```bash
cd services/webapp-react
node perf/performance_test.js [--port PORT] [--iterations N] [--seed-data]
```

**Scenarios Covered:**
1. **Home Page Load Performance** - Measures initial page load with dog data fetching and rendering
2. **Filtering Performance** - Tests various filter combinations (availability, size, case managers)
3. **Search Performance** - Tests search queries (names, breeds, case managers)
4. **Sorting Performance** - Tests sorting by name and age (ascending/descending)
5. **Bundle Size Analysis** - Analyzes production build size

### Expected File Output
Results are saved to `services/webapp-react/perf/` with timestamp:

```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "config": {
    "port": 5173,
    "iterations": 3,
    "seedData": false
  },
  "tests": [
    {
      "name": "Home Page Load Performance",
      "average": 1234.5,
      "min": 1100,
      "max": 1450,
      "avgDogCount": 8.5
    },
    {
      "name": "Filtering Performance",
      "measurements": [
        {
          "scenario": "No filters",
          "average": 45.2,
          "avgVisibleDogs": 10
        },
        {
          "scenario": "Available only",
          "average": 123.8,
          "avgVisibleDogs": 7
        }
      ]
    },
    {
      "name": "Search Performance",
      "measurements": [
        {
          "query": "Max",
          "description": "Single name search",
          "average": 89.3,
          "avgResultCount": 2
        }
      ]
    },
    {
      "name": "Sorting Performance",
      "measurements": [
        {
          "description": "Name A-Z",
          "average": 67.4,
          "avgDogCount": 10
        }
      ]
    },
    {
      "name": "Bundle Size Analysis",
      "buildSize": 1847291
    }
  ]
}
```

### Compare Runs
```bash
# Check metrics across runs
ls perf/performance_results_*.json
cat perf/performance_results_*.json | jq '.metrics.pageLoadTime.avg'
```

### Target Performance
- **Home Page Load**: `average` < 2.0 seconds
- **Filtering**: `average` < 500ms per scenario
- **Search**: `average` < 300ms per query
- **Sorting**: `average` < 200ms per sort operation
- **Bundle Size**: `buildSize` < 2MB (2000000 bytes)

## How to Add a New Perf Scenario

To add a new performance test scenario, modify `services/webapp-react/perf/performance_test.js`:

### 1. Add Scenario Method
Create a new async method in the `PerformanceTester` class following the pattern:

```javascript
async testNewFeaturePerformance() {
    console.log('🎯 Testing new feature performance...');

    const results = {
        name: 'New Feature Performance',
        measurements: []
    };

    // Define test scenarios
    const testScenarios = [
        { name: 'Scenario A', config: { /* scenario config */ } },
        { name: 'Scenario B', config: { /* scenario config */ } }
    ];

    for (const scenario of testScenarios) {
        const scenarioResults = {
            scenario: scenario.name,
            measurements: []
        };

        for (let i = 0; i < this.iterations; i++) {
            try {
                // Navigate to test page
                await this.page.goto(this.baseUrl, { waitUntil: 'networkidle' });

                const startTime = Date.now();

                // Perform the action being tested
                await this.performNewFeatureAction(scenario.config);

                // Wait for completion
                await this.page.waitForSelector('.completion-indicator', { timeout: 5000 });

                const duration = Date.now() - startTime;
                const resultMetric = await this.getResultMetric();

                scenarioResults.measurements.push({
                    duration,
                    resultMetric,
                    success: true
                });

            } catch (error) {
                scenarioResults.measurements.push({
                    duration: null,
                    resultMetric: 0,
                    success: false,
                    error: error.message
                });
            }
        }

        // Calculate averages for successful measurements
        const successfulMeasurements = scenarioResults.measurements.filter(m => m.success);
        if (successfulMeasurements.length > 0) {
            scenarioResults.average = this.calculateAverage(successfulMeasurements.map(m => m.duration));
            scenarioResults.avgResultMetric = this.calculateAverage(successfulMeasurements.map(m => m.resultMetric));
        }

        results.measurements.push(scenarioResults);
    }

    return results;
}
```

### 2. Add Helper Methods
Add any helper methods needed for your scenario:

```javascript
async performNewFeatureAction(config) {
    // Implement the action logic
    await this.page.click('[data-testid="new-feature-button"]');
    // ... additional steps
}

async getResultMetric() {
    // Return a metric for the results (count, size, etc.)
    return await this.page.locator('.result-items').count();
}
```

### 3. Wire Into Main Test Flow
Add the new test to the main `runTests()` method:

```javascript
// Test 6: New feature performance
const newFeatureTest = await this.testNewFeaturePerformance();
results.tests.push(newFeatureTest);
```

### 4. Update Expected Performance
Add target performance metrics to the "Target Performance" section above.

## Running Both Together

Use the orchestrator script for comprehensive performance testing:

```bash
./scripts/run_performance_tests.sh
```

This runs both ETL and webapp performance tests with proper environment setup.
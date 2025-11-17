/**
 * Performance test scenario definitions and thresholds.
 * Single source of truth for all performance test configurations.
 */

/**
 * Default performance test scenarios.
 * Each scenario defines actions, measurements, and iteration counts.
 */
const DEFAULT_SCENARIOS = {
  "homePageLoad": {
    "name": "Home Page Load Performance",
    "description": "Measure time to load home page and display dog data",
    "iterations": 3,
    "actions": [
      {
        "type": "navigate",
        "url": "/",
        "waitFor": "networkidle"
      },
      {
        "type": "waitForSelector",
        "selector": ".dogs-grid, .empty-state",
        "timeout": 10000
      }
    ],
    "measurements": ["loadTime", "dogCount", "authStatus"]
  },
  "filtering": {
    "name": "Filtering Performance",
    "description": "Test filtering operations with various combinations",
    "iterations": 2,
    "scenarios": [
      {
        "name": "No filters",
        "filters": {}
      },
      {
        "name": "Available only",
        "filters": { "availability": ["available"] }
      },
      {
        "name": "Small size",
        "filters": { "sizes": ["Small"] }
      }
    ],
    "actions": [
      {
        "type": "navigate",
        "url": "/",
        "waitFor": "networkidle"
      },
      {
        "type": "waitForSelector",
        "selector": ".dogs-grid, .empty-state",
        "timeout": 5000
      },
      {
        "type": "applyFilters",
        "filters": "{{scenario.filters}}"
      }
    ],
    "measurements": ["filterTime", "visibleDogs", "activeFilters"]
  },
  "search": {
    "name": "Search Performance",
    "description": "Test search functionality with different queries",
    "iterations": 2,
    "scenarios": [
      { "query": "", "description": "Empty search" },
      { "query": "Buddy", "description": "Name search" },
      { "query": "Golden", "description": "Breed search" }
    ],
    "actions": [
      {
        "type": "navigate",
        "url": "/",
        "waitFor": "networkidle"
      },
      {
        "type": "waitForSelector",
        "selector": ".dogs-grid, .empty-state",
        "timeout": 5000
      },
      {
        "type": "search",
        "query": "{{scenario.query}}"
      }
    ],
    "measurements": ["searchTime", "resultCount"]
  }
};

/**
 * Performance thresholds (contractual metrics).
 * These are enforced in CI and block merges if exceeded.
 */
const THRESHOLDS = {
  "homePageLoad": 2000,  // ms
  "filtering": 500,      // ms
  "search": 300          // ms
};

module.exports = {
  DEFAULT_SCENARIOS,
  THRESHOLDS
};


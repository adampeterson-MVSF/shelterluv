#!/usr/bin/env node

/**
 * Generate simple test report for key services (DEV-ONLY)
 * Runs: webapp unit tests, ETL tests, E2E auth test
 * Creates TESTS.txt summary and test-results.json
 *
 * Usage: node generate_test_report.js [--continue-on-error]
 *
 * This script is idempotent - running it multiple times will overwrite
 * previous results, not append to them.
 */

const { runAllTests, writeTestArtifacts } = require('./common/testRunner');

function main() {
  console.log('Generating test report...');

  // Check for --continue-on-error flag
  const continueOnError = process.argv.includes('--continue-on-error');

  runAllTests({ continueOnError })
    .then((results) => {
      // Write results to artifacts
      writeTestArtifacts(results);

      // Exit with appropriate code for CI - failures in any phase cause non-zero exit
      const allPassed = results.webapp.success && results.etl.success && results.e2e.success;
      process.exit(allPassed ? 0 : 1);
    })
    .catch((error) => {
      console.error(`❌ Test suite failed: ${error.message}`);

      // Write error results using the same artifact writing logic
      const errorResults = {
        timestamp: new Date().toISOString(),
        error: error.message,
        webapp: { success: false, exitCode: 1, output: '' },
        etl: { success: false, exitCode: 1, output: '' },
        e2e: { success: false, exitCode: 1, output: '' }
      };
      writeTestArtifacts(errorResults);
      process.exit(1);
    });
}

if (require.main === module) {
  main();
}

module.exports = { runAllTests, writeTestArtifacts };

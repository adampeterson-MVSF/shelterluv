/**
 * Unified test runner for all services.
 * Provides consistent interfaces for running tests programmatically.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

/**
 * Run tests for a specific service.
 * @param {string} serviceName - Name of the service ('webapp', 'etl', 'e2e')
 * @param {Object} options - Test options
 * @param {boolean} options.continueOnError - Continue running other tests if one fails
 * @param {string} options.cwd - Working directory override
 * @returns {Promise<Object>} Test results
 */
async function runServiceTests(serviceName, options = {}) {
  const { continueOnError = false, cwd } = options;

  const testConfigs = {
    webapp: {
      command: process.env.WEBAPP_TEST_CMD || 'npm test -- --run --reporter=json',
      cwd: cwd || 'services/webapp-react'
    },
    etl: {
      command: process.env.ETL_TEST_CMD || 'python3 -m pytest tests/ --tb=line -q',
      cwd: cwd || 'services/etl-scraper-py'
    },
    e2e: {
      command: process.env.E2E_TEST_CMD || 'npm run test:e2e -- --grep "auth"',
      cwd: cwd || 'services/webapp-react'
    }
  };

  const config = testConfigs[serviceName];
  if (!config) {
    return {
      service: serviceName,
      success: false,
      exitCode: 1,
      output: '',
      error: `Unknown service: ${serviceName}`
    };
  }

  try {
    console.log(`Running ${serviceName} tests...`);

    const execOptions = {
      encoding: 'utf8',
      maxBuffer: 1024 * 1024 * 10,
      cwd: config.cwd
    };

    const output = execSync(config.command, execOptions);

    console.log(`${serviceName} tests passed`);
    return {
      service: serviceName,
      success: true,
      exitCode: 0,
      output: output.trim(),
      error: ''
    };

  } catch (error) {
    const errorOutput = error.stdout || '';
    const errorMessage = error.stderr || error.message || '';

    console.log(`${serviceName} tests failed (exit code: ${error.status || 1})`);

    if (!continueOnError) {
      throw new Error(`${serviceName} tests failed: ${errorMessage}`);
    }

    return {
      service: serviceName,
      success: false,
      exitCode: error.status || 1,
      output: errorOutput.trim(),
      error: errorMessage.trim()
    };
  }
}

/**
 * Run all tests for the project.
 * @param {Object} options - Test options
 * @param {boolean} options.continueOnError - Continue running tests even if some fail
 * @returns {Promise<Object>} Complete test results
 */
async function runAllTests(options = {}) {
  const { continueOnError = false } = options;

  console.log('Running test suite...');

  const results = {
    timestamp: new Date().toISOString(),
    webapp: await runServiceTests('webapp', { continueOnError }),
    etl: await runServiceTests('etl', { continueOnError }),
    e2e: await runServiceTests('e2e', { continueOnError })
  };

  return results;
}

/**
 * Write test results to artifacts directory.
 * @param {Object} results - Test results object
 */
function writeTestArtifacts(results) {
  // Ensure artifacts directory exists
  if (!fs.existsSync('artifacts')) {
    fs.mkdirSync('artifacts');
  }

  // Write structured JSON results for CI consumption
  fs.writeFileSync('artifacts/test-results.json', JSON.stringify(results, null, 2));

  // Write human-readable TESTS.txt summary
  const testOutput = [
    '================ REACT WEBAPP TESTS ================',
    '',
    results.webapp.output,
    '',
    '================ ETL TESTS ================',
    '',
    results.etl.output,
    '',
    '================ E2E AUTH TESTS ================',
    '',
    results.e2e.output,
    '',
    '================ SUMMARY ================',
    '',
    `Webapp tests: ${results.webapp.success ? 'PASSED' : 'FAILED'} (exit code: ${results.webapp.exitCode})`,
    `ETL tests: ${results.etl.success ? 'PASSED' : 'FAILED'} (exit code: ${results.etl.exitCode})`,
    `E2E tests: ${results.e2e.success ? 'PASSED' : 'FAILED'} (exit code: ${results.e2e.exitCode})`,
    '',
    `Overall: ${results.webapp.success && results.etl.success && results.e2e.success ? 'ALL PASSED' : 'SOME FAILED'}`
  ].join('\n');

  fs.writeFileSync('artifacts/TESTS.txt', testOutput);
}

module.exports = {
  runServiceTests,
  runAllTests,
  writeTestArtifacts
};

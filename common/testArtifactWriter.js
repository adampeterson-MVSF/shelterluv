/**
 * Test artifact writing functionality.
 * Handles writing test results to files.
 * Keeps API small: single writeTestArtifacts function.
 * Extracts formatting into pure helpers for testability.
 */

const fs = require('fs');

/**
 * Format test output with stderr if present.
 * Pure function - no side effects.
 * @param {Object} result - Test result with stdout/stderr
 * @returns {string} Formatted output string
 */
function formatTestOutput(result) {
  let output = result.stdout || '';
  if (result.stderr && result.stderr.trim()) {
    output += (output ? '\n\n--- STDERR ---\n' : '') + result.stderr;
  }
  return output;
}

/**
 * Format test summary section.
 * Pure function - no side effects.
 * @param {Object} results - Test results object
 * @returns {string} Formatted summary string
 */
function formatTestSummary(results) {
  const sections = [
    '================ REACT WEBAPP TESTS ================',
    '',
    formatTestOutput(results.webapp),
    '',
    '================ ETL TESTS ================',
    '',
    formatTestOutput(results.etl),
    '',
    '================ E2E AUTH TESTS ================',
    '',
    formatTestOutput(results.e2e),
    '',
    '================ SUMMARY ================',
    '',
    `Webapp tests: ${results.webapp.success ? 'PASSED' : 'FAILED'} (exit code: ${results.webapp.exitCode})`,
    `ETL tests: ${results.etl.success ? 'PASSED' : 'FAILED'} (exit code: ${results.etl.exitCode})`,
    `E2E tests: ${results.e2e.success ? 'PASSED' : 'FAILED'} (exit code: ${results.e2e.exitCode})`,
    '',
    `Overall: ${results.webapp.success && results.etl.success && results.e2e.success ? 'ALL PASSED' : 'SOME FAILED'}`
  ];
  
  return sections.join('\n');
}

/**
 * Write test results to artifacts directory.
 * Robust to partial failures: always writes something, never throws before writing.
 * @param {Object} results - Test results object
 * @param {Object} options - Write options
 * @param {Function} options.writeFile - File writing function (injected for testability)
 * @param {Function} options.mkdir - Directory creation function (injected for testability)
 * @param {Function} options.exists - File existence check function (injected for testability)
 */
function writeTestArtifacts(results, options = {}) {
  const {
    writeFile = (path, content) => fs.writeFileSync(path, content),
    mkdir = (path) => fs.mkdirSync(path),
    exists = (path) => fs.existsSync(path)
  } = options;

  // Ensure artifacts directory exists
  if (!exists('artifacts')) {
    mkdir('artifacts');
  }

  // Write structured JSON results for CI consumption
  // Always write JSON first (most important for CI)
  try {
    writeFile('artifacts/test-results.json', JSON.stringify(results, null, 2));
  } catch (error) {
    // If JSON write fails, still try to write text summary
    console.error('Failed to write JSON results:', error.message);
  }

  // Write human-readable TESTS.txt summary
  try {
    const testOutput = formatTestSummary(results);
    writeFile('artifacts/TESTS.txt', testOutput);
  } catch (error) {
    // If text write fails, at least JSON was written
    console.error('Failed to write text summary:', error.message);
  }
}

module.exports = {
  writeTestArtifacts,
  formatTestOutput,
  formatTestSummary
};

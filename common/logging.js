/**
 * Shared logging utilities for CLI scripts.
 * Consistent formatting and error handling.
 */

/**
 * Log a success message to stdout.
 * @param {string} message - Success message to log
 */
function logSuccess(message) {
  console.log(`✅ ${message}`);
}

/**
 * Log an error message to stderr.
 * @param {string} message - Error message to log
 */
function logError(message) {
  console.error(`❌ ${message}`);
}

/**
 * Log an info message to stdout.
 * @param {string} message - Info message to log
 */
function logInfo(message) {
  console.log(`ℹ️  ${message}`);
}

/**
 * Log a warning message to stdout.
 * @param {string} message - Warning message to log
 */
function logWarning(message) {
  console.log(`⚠️  ${message}`);
}

module.exports = {
  logSuccess,
  logError,
  logInfo,
  logWarning
};

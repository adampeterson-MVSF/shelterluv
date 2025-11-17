/**
 * Test execution and result processing.
 * Handles running commands and processing outputs.
 */

const { execSync } = require('child_process');
const {
  buildWebappTestCommand,
  buildEtlTestCommand,
  buildWebappE2eTestCommand,
  buildEtlE2eTestCommand
} = require('./testCommandBuilder');

const { writeTestArtifacts } = require('./testArtifactWriter');

/**
 * Execute a test command and process results.
 * Always captures stdout, stderr, and exit code. Never calls process.exit.
 * @param {Object} commandConfig - Command configuration from builder
 * @param {Object} options - Execution options
 * @param {boolean} options.continueOnError - Continue on error instead of throwing
 * @param {Function} options.log - Logging function (injected for testability)
 * @returns {Object} Test results with success, exitCode, stdout, stderr
 */
function executeTestCommand(commandConfig, options = {}) {
  const { continueOnError = false, log = console.log } = options;
  const { command, options: execOptions, service } = commandConfig;

  // Ensure we capture both stdout and stderr
  const execOpts = {
    encoding: 'utf8',
    stdio: ['pipe', 'pipe', 'pipe'], // stdin, stdout, stderr
    ...execOptions
  };

  try {
    log(`Running ${service} tests...`);

    const output = execSync(command, execOpts);
    const stdout = output.toString().trim();
    const stderr = '';

    log(`${service} tests passed`);
    return {
      service,
      success: true,
      exitCode: 0,
      stdout,
      stderr
    };

  } catch (error) {
    // execSync throws on non-zero exit, but we capture output
    const stdout = (error.stdout || '').toString().trim();
    const stderr = (error.stderr || error.message || '').toString().trim();
    const exitCode = error.status || 1;

    log(`${service} tests failed (exit code: ${exitCode})`);

    if (!continueOnError) {
      throw new Error(`${service} tests failed: ${stderr || 'Unknown error'}`);
    }

    return {
      service,
      success: false,
      exitCode,
      stdout,
      stderr,
      output: stdout, // Legacy field for backward compatibility
      error: stderr // Legacy field for backward compatibility
    };
  }
}

/**
 * Run webapp tests.
 * @param {Object} options - Test options
 * @param {boolean} options.continueOnError - Continue running other tests if one fails
 * @param {string} options.cwd - Working directory override
 * @param {Function} options.log - Logging function override
 * @returns {Object} Test results
 */
function runWebappTests(options = {}) {
  const { cwd, ...execOptions } = options;
  const commandConfig = buildWebappTestCommand({ cwd });
  return executeTestCommand(commandConfig, execOptions);
}

/**
 * Run ETL tests.
 * @param {Object} options - Test options
 * @param {boolean} options.continueOnError - Continue running other tests if one fails
 * @param {string} options.cwd - Working directory override
 * @param {Function} options.log - Logging function override
 * @returns {Object} Test results
 */
function runEtlTests(options = {}) {
  const { cwd, ...execOptions } = options;
  const commandConfig = buildEtlTestCommand({ cwd });
  return executeTestCommand(commandConfig, execOptions);
}

/**
 * Run webapp E2E tests.
 * @param {Object} options - Test options
 * @param {boolean} options.continueOnError - Continue running other tests if one fails
 * @param {string} options.cwd - Working directory override
 * @param {Function} options.log - Logging function override
 * @returns {Object} Test results
 */
function runWebappE2eTests(options = {}) {
  const { cwd, ...execOptions } = options;
  const commandConfig = buildWebappE2eTestCommand({ cwd });
  return executeTestCommand(commandConfig, execOptions);
}

/**
 * Run ETL E2E tests.
 * @param {Object} options - Test options
 * @param {boolean} options.continueOnError - Continue running other tests if one fails
 * @param {string} options.cwd - Working directory override
 * @param {Function} options.log - Logging function override
 * @returns {Object} Test results
 */
function runEtlE2eTests(options = {}) {
  const { cwd, ...execOptions } = options;
  const commandConfig = buildEtlE2eTestCommand({ cwd });
  return executeTestCommand(commandConfig, execOptions);
}


/**
 * Run all tests for the project.
 * @param {Object} options - Test options
 * @param {boolean} options.continueOnError - Continue running tests even if some fail
 * @param {Function} options.log - Logging function override
 * @returns {Object} Complete test results
 */
function runAllTests(options = {}) {
  const { continueOnError = false, log = console.log } = options;

  log('Running test suite...');

  const results = {
    timestamp: new Date().toISOString(),
    webapp: runWebappTests({ continueOnError, log }),
    etl: runEtlTests({ continueOnError, log }),
    e2e: runWebappE2eTests({ continueOnError, log })
  };

  return Promise.resolve(results);
}

module.exports = {
  executeTestCommand,
  runWebappTests,
  runEtlTests,
  runWebappE2eTests,
  runEtlE2eTests,
  runAllTests,
  writeTestArtifacts
};
#!/usr/bin/env node

/**
 * Test Report Generation Tool
 * Runs comprehensive test suite and generates reports.
 *
 * Usage:
 *   node generate_test_report.js run     # Run all tests and generate report
 *   node generate_test_report.js --help  # Show help
 */

const { runAllTests, runEtlE2eTests, writeTestArtifacts } = require('./common/testRunner');

const COMMANDS = {
  run: {
    description: 'Run all tests and generate test report',
    handler: runTestReport
  },
  'etl-e2e': {
    description: 'Run ETL E2E tests (requires E2E_LIVE_DB=1)',
    handler: runEtlE2eTestReport
  }
};

function showHelp() {
  console.log('Test Report Generation Tool\n');
  console.log('Usage: node generate_test_report.js <command> [options]\n');
  console.log('Commands:');
  Object.entries(COMMANDS).forEach(([cmd, info]) => {
    console.log(`  ${cmd.padEnd(8)} ${info.description}`);
  });
  console.log('\nOptions:');
  console.log('  --help, -h            Show this help');
  console.log('  --continue-on-error   Continue testing even if some tests fail');
  console.log('  --json                Output results as JSON to stdout');
}

/**
 * Run all tests and generate report.
 * Thin orchestrator around testRunner - handles I/O and exit codes only.
 * @param {object} options - Options object
 * @param {boolean} options.json - Output JSON to stdout (does not write artifacts)
 * @param {boolean} options.continueOnError - Continue testing even if some fail
 * @returns {Promise<boolean>} True if all tests passed
 */
async function runTestReport(options = {}) {
  if (!options.json) {
    console.log('Generating test report...');
  }

  try {
    const results = await runAllTests({ continueOnError: options.continueOnError });

    // Write results to artifacts ONLY if not JSON mode
    // JSON mode should never write artifacts (pure stdout)
    if (!options.json) {
      writeTestArtifacts(results);
    } else {
      // JSON mode: output to stdout only, no artifacts
      console.log(JSON.stringify(results, null, 2));
    }

    // Return success status (caller handles exit code)
    const allPassed = results.webapp.success && results.etl.success && results.e2e.success;
    return allPassed;

  } catch (error) {
    if (!options.json) {
      console.error(`❌ Test suite failed: ${error.message}`);
    }

    // Create error results structure
    const errorResults = {
      timestamp: new Date().toISOString(),
      error: error.message,
      webapp: { success: false, exitCode: 1, stdout: '', stderr: error.message },
      etl: { success: false, exitCode: 1, stdout: '', stderr: error.message },
      e2e: { success: false, exitCode: 1, stdout: '', stderr: error.message }
    };

    // Write artifacts ONLY if not JSON mode
    if (options.json) {
      console.log(JSON.stringify(errorResults, null, 2));
    } else {
      writeTestArtifacts(errorResults);
    }

    return false;
  }
}

async function runEtlE2eTestReport(options = {}) {
  if (!options.json) {
    console.log('Running ETL E2E tests...');
  }

  try {
    const results = await runEtlE2eTests({ continueOnError: options.continueOnError });

    if (options.json) {
      console.log(JSON.stringify(results, null, 2));
    } else {
      console.log(results.stdout || '');
      if (results.stderr) {
        console.error(results.stderr);
      }
    }

    return results.success;

  } catch (error) {
    if (!options.json) {
      console.error(`❌ ETL E2E tests failed: ${error.message}`);
    }

    const errorResults = {
      timestamp: new Date().toISOString(),
      service: 'etl-e2e',
      success: false,
      exitCode: 1,
      stdout: '',
      stderr: error.message
    };

    if (options.json) {
      console.log(JSON.stringify(errorResults, null, 2));
    }

    return false;
  }
}

/**
 * Main entrypoint - handles CLI args and exit codes.
 * Never swallows non-zero exit codes - always propagates them.
 */
function main() {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h') || args.length === 0) {
    showHelp();
    process.exit(0);
    return;
  }

  const command = args[0];
  const options = {
    continueOnError: args.includes('--continue-on-error'),
    json: args.includes('--json')
  };

  if (!COMMANDS[command]) {
    console.error(`Unknown command: ${command}`);
    console.log('\nAvailable commands:');
    Object.keys(COMMANDS).forEach(cmd => console.log(`  ${cmd}`));
    process.exit(1);
    return;
  }

  COMMANDS[command].handler(options)
    .then(success => {
      // Exit with 0 on success, 1 on failure
      // Never swallow exit codes - let CI/tooling detect failures
      process.exit(success ? 0 : 1);
    })
    .catch(error => {
      console.error(`❌ Command execution failed: ${error.message}`);
      // Always exit with non-zero on unhandled errors
      process.exit(1);
    });
}

if (require.main === module) {
  main();
}

module.exports = { runAllTests, writeTestArtifacts };

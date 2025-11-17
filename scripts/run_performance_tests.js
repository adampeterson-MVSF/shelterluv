#!/usr/bin/env node

/**
 * Unified Performance Testing Tool
 * Runs performance tests across all services with consistent interfaces.
 *
 * For detailed performance testing documentation, see PERFORMANCE_README.md
 *
 * Usage:
 *   node scripts/run_performance_tests.js          # Run all performance tests
 *   node scripts/run_performance_tests.js etl      # Run only ETL performance tests
 *   node scripts/run_performance_tests.js webapp   # Run only webapp performance tests
 *   node scripts/run_performance_tests.js --help   # Show help
 */

const { spawn } = require('child_process');
const path = require('path');
const { assertSafe } = require('../common/devScriptSafety');
const { getProjectId } = require('../common/firebaseConfig');

/**
 * Performance test scenario configurations.
 * Each scenario defines how to run a performance test for a service.
 */
const PERFORMANCE_SCENARIOS = [
  {
    key: 'etl',
    name: 'ETL Pipeline',
    command: 'python3',
    args: ['perf/pipeline_performance_test.py', '--dogs', '10'],
    cwd: path.join(__dirname, '..', 'services', 'etl_scraper_py'),
    description: 'Test ETL pipeline performance with 10 dogs'
  },
  {
    key: 'webapp',
    name: 'Webapp',
    command: 'node',
    args: ['perf/performance_test.js'],
    cwd: path.join(__dirname, '..', 'services', 'webapp-react'),
    description: 'Test webapp performance and responsiveness'
  }
];

// Convert to lookup map for backward compatibility
const SERVICES = Object.fromEntries(
  PERFORMANCE_SCENARIOS.map(scenario => [scenario.key, scenario])
);

function showHelp() {
  console.log('Unified Performance Testing Tool\n');
  console.log('Usage: node scripts/run_performance_tests.js [service] [options]\n');
  console.log('Services:');
  Object.entries(SERVICES).forEach(([key, service]) => {
    console.log(`  ${key.padEnd(8)} ${service.name} - ${service.description}`);
  });
  console.log('  (no service specified runs all)\n');
  console.log('Options:');
  console.log('  --help, -h           Show this help');
  console.log('  --verbose, -v        Enable verbose output');
  console.log('  --json               Output results as JSON');
  console.log('  --continue-on-error  Continue testing even if one service fails');
}

async function runServicePerformanceTest(serviceKey, options = {}) {
  const service = SERVICES[serviceKey];

  if (!options.json) {
    console.log(`🚀 Running ${service.name} performance test...`);
    if (options.verbose) {
      console.log(`Command: ${service.command} ${service.args.join(' ')}`);
    }
  }

  return new Promise((resolve) => {
    const child = spawn(service.command, service.args, {
      cwd: service.cwd,
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    child.on('close', (code) => {
      const success = code === 0;

      if (!options.json) {
        if (success) {
          console.log(`✅ ${service.name} performance test completed successfully`);
          if (options.verbose && stdout) {
            console.log('Output:', stdout.slice(0, 500) + (stdout.length > 500 ? '...' : ''));
          }
        } else {
          console.error(`❌ ${service.name} performance test failed`);
          if (stderr) {
            console.error('Error:', stderr);
          }
        }
      }

      resolve({
        service: serviceKey,
        name: service.name,
        success,
        exitCode: code,
        stdout,
        stderr
      });
    });

    child.on('error', (error) => {
      if (!options.json) {
        console.error(`❌ ${service.name} performance test failed to start`);
        console.error('Error:', error.message);
      }

      resolve({
        service: serviceKey,
        name: service.name,
        success: false,
        exitCode: null,
        stdout,
        stderr: error.message
      });
    });
  });
}

/**
 * Validate environment is safe for performance testing.
 * Uses devScriptSafety for consistent safety checks.
 * @param {Object} options - Options object
 * @returns {boolean} True if safe, false otherwise
 */
function validateEnvironment(options = {}) {
  try {
    const projectId = getProjectId('admin');
    assertSafe(projectId, { allowDestructive: false });
    return true;
  } catch (error) {
    const errorMsg = error.message;
    if (options.json) {
      console.log(JSON.stringify({
        success: false,
        error: errorMsg,
        timestamp: new Date().toISOString()
      }));
    } else {
      console.error('❌ ERROR:', errorMsg);
    }
    return false;
  }
}

async function runAllPerformanceTests(options = {}) {
  if (!options.json) {
    console.log('🔍 Unified Performance Testing Suite');
    console.log('=====================================\n');
  }

  // Environment safety check
  if (!validateEnvironment(options)) {
    return false;
  }

  const projectId = process.env.GCP_PROJECT || process.env.FIREBASE_PROJECT_ID;
  if (!options.json) {
    console.log('🔍 Environment safety check passed');
    console.log(`GCP_PROJECT: ${projectId || 'not set'}\n`);
  }

  const results = [];
  const servicesToRun = Object.keys(SERVICES);

  for (const serviceKey of servicesToRun) {
    const result = await runServicePerformanceTest(serviceKey, options);
    results.push(result);

    if (!result.success && !options.continueOnError) {
      if (!options.json) {
        console.log(`\n❌ Stopping due to failure in ${result.name}`);
      }
      break;
    }

    if (!options.json) {
      console.log(''); // Add spacing between tests
    }
  }

  // Summary
  const successful = results.filter(r => r.success).length;
  const total = results.length;
  const overallSuccess = successful === total;

  if (options.json) {
    console.log(JSON.stringify({
      success: overallSuccess,
      timestamp: new Date().toISOString(),
      environment: {
        GCP_PROJECT: projectId,
        FIREBASE_PROJECT_ID: projectId
      },
      summary: {
        passed: successful,
        total: total,
        failed: total - successful
      },
      results: results
    }));
  } else {
    console.log('=====================================');
    console.log(`📊 Performance Test Summary: ${successful}/${total} services passed`);

    results.forEach(result => {
      const status = result.success ? '✅' : '❌';
      console.log(`${status} ${result.name}`);
    });

    if (overallSuccess) {
      console.log('\n🎉 All performance tests completed successfully!');
    } else {
      console.log('\n❌ Some performance tests failed');
      if (!options.continueOnError) {
        console.log('Run with --continue-on-error to see all failures');
      }
    }
  }

  return overallSuccess;
}

/**
 * Parse command line arguments into options and service keys.
 * @param {string[]} args - Command line arguments
 * @returns {{options: Object, serviceKeys: string[]}}
 */
function parseArgs(args) {
  const options = {
    verbose: args.includes('--verbose') || args.includes('-v'),
    json: args.includes('--json'),
    continueOnError: args.includes('--continue-on-error')
  };

  const serviceKeys = args.filter(arg => !arg.startsWith('--'));
  return { options, serviceKeys };
}

async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h')) {
    showHelp();
    process.exit(0);
    return;
  }

  const { options, serviceKeys } = parseArgs(args);

  // Run all services if none specified
  if (serviceKeys.length === 0) {
    const success = await runAllPerformanceTests(options);
    process.exit(success ? 0 : 1);
    return;
  }

  // Run specific services
  let allSuccess = true;
  for (const serviceKey of serviceKeys) {
    if (!SERVICES[serviceKey]) {
      console.error(`Unknown service: ${serviceKey}`);
      console.log('Available services:', Object.keys(SERVICES).join(', '));
      process.exit(1);
      return;
    }

    const result = await runServicePerformanceTest(serviceKey, options);
    if (!result.success) {
      allSuccess = false;
      if (!options.continueOnError) {
        break;
      }
    }
    if (!options.json) {
      console.log('');
    }
  }

  process.exit(allSuccess ? 0 : 1);
}

if (require.main === module) {
  main().catch(error => {
    console.error('❌ Performance test execution failed:', error.message);
    process.exit(1);
  });
}

module.exports = { runAllPerformanceTests, runServicePerformanceTest };

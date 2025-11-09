#!/usr/bin/env node

/**
 * Unified Performance Testing Tool
 * Runs performance tests across all services with consistent interfaces.
 *
 * Usage:
 *   node scripts/run_performance_tests.js          # Run all performance tests
 *   node scripts/run_performance_tests.js etl      # Run only ETL performance tests
 *   node scripts/run_performance_tests.js webapp   # Run only webapp performance tests
 *   node scripts/run_performance_tests.js --help   # Show help
 */

const { runCommand } = require('./lib/firebaseTools');
const path = require('path');

const SERVICES = {
  etl: {
    name: 'ETL Pipeline',
    command: 'cd services/etl-scraper-py && python perf/pipeline_performance_test.py --dogs 10',
    cwd: path.join(__dirname, '..', 'services', 'etl-scraper-py'),
    description: 'Test ETL pipeline performance with 10 dogs'
  },
  webapp: {
    name: 'Webapp',
    command: 'cd services/webapp-react && node perf/performance_test.js',
    cwd: path.join(__dirname, '..', 'services', 'webapp-react'),
    description: 'Test webapp performance and responsiveness'
  }
};

function showHelp() {
  console.log('Unified Performance Testing Tool\n');
  console.log('Usage: node scripts/run_performance_tests.js [service] [options]\n');
  console.log('Services:');
  Object.entries(SERVICES).forEach(([key, service]) => {
    console.log(`  ${key.padEnd(8)} ${service.name} - ${service.description}`);
  });
  console.log('  (no service specified runs all)\n');
  console.log('Options:');
  console.log('  --help, -h    Show this help');
  console.log('  --verbose, -v Enable verbose output');
  console.log('  --continue-on-error  Continue testing even if one service fails');
}

async function runServicePerformanceTest(serviceKey, options = {}) {
  const service = SERVICES[serviceKey];
  console.log(`🚀 Running ${service.name} performance test...`);
  if (options.verbose) {
    console.log(`Command: ${service.command}`);
  }

  const result = runCommand(service.command, {
    cwd: service.cwd,
    maxBuffer: 1024 * 1024 * 10 // 10MB buffer for performance output
  });

  if (result.success) {
    console.log(`✅ ${service.name} performance test completed successfully`);
    if (options.verbose && result.output) {
      console.log('Output:', result.output.slice(0, 500) + (result.output.length > 500 ? '...' : ''));
    }
  } else {
    console.error(`❌ ${service.name} performance test failed`);
    if (result.error) {
      console.error('Error:', result.error);
    }
  }

  return result.success;
}

async function runAllPerformanceTests(options = {}) {
  console.log('🔍 Unified Performance Testing Suite');
  console.log('=====================================\n');

  // Environment safety checks
  const firebaseEnv = process.env.FIREBASE_ENV;
  const gcpProject = process.env.GOOGLE_CLOUD_PROJECT;

  if (firebaseEnv === 'prod' || (gcpProject && gcpProject.includes('prod'))) {
    console.error('❌ ERROR: Cannot run performance tests against production environment');
    console.error('Set FIREBASE_ENV=staging and GOOGLE_CLOUD_PROJECT to a safe project');
    return false;
  }

  console.log('🔍 Environment safety check passed');
  console.log(`FIREBASE_ENV: ${firebaseEnv || 'not set'}`);
  console.log(`GOOGLE_CLOUD_PROJECT: ${gcpProject || 'not set'}\n`);

  const results = [];
  const servicesToRun = Object.keys(SERVICES);

  for (const serviceKey of servicesToRun) {
    const success = await runServicePerformanceTest(serviceKey, options);

    results.push({
      service: serviceKey,
      name: SERVICES[serviceKey].name,
      success
    });

    if (!success && !options.continueOnError) {
      console.log(`\n❌ Stopping due to failure in ${SERVICES[serviceKey].name}`);
      break;
    }

    console.log(''); // Add spacing between tests
  }

  // Summary
  const successful = results.filter(r => r.success).length;
  const total = results.length;

  console.log('=====================================');
  console.log(`📊 Performance Test Summary: ${successful}/${total} services passed`);

  results.forEach(result => {
    const status = result.success ? '✅' : '❌';
    console.log(`${status} ${result.name}`);
  });

  if (successful === total) {
    console.log('\n🎉 All performance tests completed successfully!');
  } else {
    console.log('\n❌ Some performance tests failed');
    if (!options.continueOnError) {
      console.log('Run with --continue-on-error to see all failures');
    }
  }

  return successful === total;
}

async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h')) {
    showHelp();
    return;
  }

  const options = {
    verbose: args.includes('--verbose') || args.includes('-v'),
    continueOnError: args.includes('--continue-on-error')
  };

  // Filter out option flags to get service names
  const serviceArgs = args.filter(arg => !arg.startsWith('--'));

  if (serviceArgs.length === 0) {
    // Run all services
    const success = await runAllPerformanceTests(options);
    process.exit(success ? 0 : 1);
  } else {
    // Run specific services
    let allSuccess = true;

    for (const serviceArg of serviceArgs) {
      if (!SERVICES[serviceArg]) {
        console.error(`Unknown service: ${serviceArg}`);
        console.log('Available services:', Object.keys(SERVICES).join(', '));
        process.exit(1);
      }

      const success = await runServicePerformanceTest(serviceArg, options);
      if (!success) {
        allSuccess = false;
        if (!options.continueOnError) {
          break;
        }
      }
      console.log('');
    }

    process.exit(allSuccess ? 0 : 1);
  }
}

if (require.main === module) {
  main().catch(error => {
    console.error('❌ Performance test execution failed:', error.message);
    process.exit(1);
  });
}

module.exports = { runAllPerformanceTests, runServicePerformanceTest };

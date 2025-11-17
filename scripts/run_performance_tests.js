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

const SERVICES = {
  etl: {
    name: 'ETL Pipeline',
    command: 'python',
    args: ['perf/pipeline_performance_test.py', '--dogs', '10'],
    cwd: path.join(__dirname, '..', 'services', 'etl-scraper-py'),
    description: 'Test ETL pipeline performance with 10 dogs'
  },
  webapp: {
    name: 'Webapp',
    command: 'node',
    args: ['perf/performance_test.js'],
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

async function runAllPerformanceTests(options = {}) {
  if (!options.json) {
    console.log('🔍 Unified Performance Testing Suite');
    console.log('=====================================\n');
  }

  // Environment safety checks
  const firebaseEnv = process.env.FIREBASE_ENV;
  const gcpProject = process.env.GOOGLE_CLOUD_PROJECT;

  if (firebaseEnv === 'prod' || (gcpProject && gcpProject.includes('prod'))) {
    const errorMsg = 'Cannot run performance tests against production environment';
    if (options.json) {
      console.log(JSON.stringify({
        success: false,
        error: errorMsg,
        timestamp: new Date().toISOString()
      }));
    } else {
      console.error('❌ ERROR:', errorMsg);
      console.error('Set FIREBASE_ENV=staging and GOOGLE_CLOUD_PROJECT to a safe project');
    }
    return false;
  }

  if (!options.json) {
    console.log('🔍 Environment safety check passed');
    console.log(`FIREBASE_ENV: ${firebaseEnv || 'not set'}`);
    console.log(`GOOGLE_CLOUD_PROJECT: ${gcpProject || 'not set'}\n`);
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
        FIREBASE_ENV: firebaseEnv,
        GOOGLE_CLOUD_PROJECT: gcpProject
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

async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h')) {
    showHelp();
    return;
  }

  const options = {
    verbose: args.includes('--verbose') || args.includes('-v'),
    json: args.includes('--json'),
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

/**
 * Performance test result formatting and output.
 * Pure formatting functions - no side effects except console/file I/O.
 */

const fs = require('fs');
const path = require('path');
const { THRESHOLDS } = require('./scenarios');

/**
 * Calculate average of numbers array.
 * @param {number[]} numbers - Array of numbers
 * @returns {number} Average value
 */
function calculateAverage(numbers) {
  if (numbers.length === 0) return 0;
  return numbers.reduce((sum, num) => sum + num, 0) / numbers.length;
}

/**
 * Print formatted performance test summary to console.
 * @param {Object} results - Test results object
 */
function printSummary(results) {
  console.log('\n' + '='.repeat(60));
  console.log('PERFORMANCE TEST SUMMARY');
  console.log('='.repeat(60));

  Object.entries(results.results).forEach(([key, result]) => {
    console.log(`\n${result.name}:`);
    console.log(`  ${result.description}`);

    if (result.measurements && result.measurements.length > 0) {
      result.measurements.forEach(measurement => {
        if (measurement.scenario) {
          console.log(`  ${measurement.scenario}:`);
          if (measurement.average !== undefined) {
            console.log(`    Average: ${measurement.average.toFixed(2)}ms`);
            if (measurement.successRate !== undefined) {
              console.log(`    Success Rate: ${measurement.successRate.toFixed(1)}%`);
            }
          }
        } else {
          // Individual measurements
          const successful = measurement.filter(m => m.success);
          if (successful.length > 0) {
            const avgDuration = calculateAverage(successful.map(m => m.duration));
            console.log(`    Average: ${avgDuration.toFixed(2)}ms (${successful.length}/${measurement.length} successful)`);
          }
        }
      });
    }
  });

  console.log('\n✅ Performance testing completed');
  console.log('\n💡 Performance thresholds:');
  Object.entries(THRESHOLDS).forEach(([key, threshold]) => {
    console.log(`   - ${key}: < ${threshold}ms`);
  });
}

/**
 * Save test results to JSON file.
 * @param {Object} results - Test results object
 * @param {string} dirPath - Directory to save file in (default: __dirname)
 */
function saveResults(results, dirPath = __dirname) {
  const filename = `performance_results_${Date.now()}.json`;
  const filepath = path.join(dirPath, filename);

  try {
    fs.writeFileSync(filepath, JSON.stringify(results, null, 2));
    console.log(`📄 Results saved to: ${filename}`);
  } catch (error) {
    console.error('❌ Failed to save results:', error.message);
  }
}

module.exports = {
  calculateAverage,
  printSummary,
  saveResults
};


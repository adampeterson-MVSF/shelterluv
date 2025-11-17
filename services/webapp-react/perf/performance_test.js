#!/usr/bin/env node

/**
 * Performance testing CLI wrapper for ShelterLuv React webapp.
 *
 * ⚠️  DEVELOPMENT ONLY - DO NOT USE IN PRODUCTION ⚠️
 *
 * Thin CLI wrapper that coordinates runner, scenarios, and reporters.
 *
 * Usage:
 *   node performance_test.js [--config CONFIG_FILE] [--json] [--port PORT]
 *
 * Options:
 *   --config CONFIG_FILE: Path to scenarios config file (default: scenarios.json)
 *   --json: Output only JSON results (no console output)
 *   --port PORT: Port where dev server is running (default: 5173)
 */

const http = require('http');
const fs = require('fs');
const { DEFAULT_SCENARIOS } = require('./scenarios');
const { PerformanceTester } = require('./runner');
const { printSummary, saveResults } = require('./reporters');

/**
 * Check if dev server is running on specified port.
 * @param {number} port - Port number to check
 * @returns {Promise<boolean>} True if server is running
 */
async function checkDevServer(port) {
    return new Promise((resolve) => {
        const req = http.request({
            hostname: 'localhost',
            port: port,
            path: '/',
            method: 'GET',
            timeout: 2000
        }, (res) => {
            resolve(true);
        });

        req.on('error', () => resolve(false));
        req.on('timeout', () => {
            req.destroy();
            resolve(false);
        });

        req.end();
    });
}

/**
 * Load scenarios from config file if specified.
 * @param {string} configPath - Path to config file
 * @returns {Object} Scenarios object
 */
function loadScenarios(configPath) {
    if (!configPath) return DEFAULT_SCENARIOS;

    try {
        const configFile = fs.readFileSync(configPath, 'utf8');
        return JSON.parse(configFile);
    } catch (error) {
        console.error(`❌ Failed to load config file ${configPath}:`, error.message);
        process.exit(1);
    }
}

/**
 * Parse command line arguments into options object.
 * @param {string[]} args - Command line arguments
 * @returns {Object} Parsed options
 */
function parseArgs(args) {
    const options = {};

    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--config':
                options.configPath = args[++i];
                break;
            case '--json':
                options.jsonOnly = true;
                break;
            case '--port':
                options.port = parseInt(args[++i]);
                break;
            default:
                if (args[i].startsWith('--')) {
                    console.error(`Unknown option: ${args[i]}`);
                    console.error('Usage: node performance_test.js [--config CONFIG_FILE] [--json] [--port PORT]');
                    process.exit(1);
                }
        }
    }

    return options;
}

/**
 * Validate environment is safe for performance testing.
 */
function validateEnvironment() {
    if (process.env.NODE_ENV === 'production') {
        console.error('❌ PRODUCTION SAFETY CHECK FAILED ❌');
        console.error('Performance tests should never run in production environment.');
        console.error('This script is for development/testing only.');
        process.exit(1);
    }
}

// Main execution
async function main() {
    validateEnvironment();

    const options = parseArgs(process.argv.slice(2));
    const scenarios = loadScenarios(options.configPath);
    const tester = new PerformanceTester({ ...options, scenarios });

    const serverRunning = await checkDevServer(tester.port);
    if (!serverRunning) {
        const errorMsg = `❌ Dev server not running on port ${tester.port}`;
        if (tester.jsonOnly) {
            console.log(JSON.stringify({ error: errorMsg }, null, 2));
        } else {
            console.log(errorMsg);
            console.log('💡 Start the dev server first:');
            console.log('   cd services/webapp-react && npm run dev');
        }
        process.exit(1);
    }

    const results = await tester.runScenarios();

    // Output results
    if (tester.jsonOnly) {
        console.log(JSON.stringify(results, null, 2));
    } else {
        printSummary(results);
        saveResults(results);
    }
}

// Run if called directly
if (require.main === module) {
    main().catch(console.error);
}

module.exports = { PerformanceTester };

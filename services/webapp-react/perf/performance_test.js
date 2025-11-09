#!/usr/bin/env node

/**
 * Performance testing script for ShelterLuv React webapp.
 *
 * ⚠️  DEVELOPMENT ONLY - DO NOT USE IN PRODUCTION ⚠️
 *
 * This script is for local development and testing only. It should never be
 * imported or executed in production environments.
 *
 * This script measures the performance of the Home page with real dog data
 * and filtering operations using Playwright browser automation.
 *
 * Usage:
 *   node performance_test.js [--port PORT] [--iterations N] [--seed-data]
 *
 * Options:
 *   --port PORT: Port where dev server is running (default: 5173)
 *   --iterations N: Number of test iterations (default: 3)
 *   --seed-data: Seed test dog data before running performance tests
 */

const { execSync, spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

class PerformanceTester {
    constructor(options = {}) {
        this.port = options.port || 5173;
        this.iterations = options.iterations || 3; // Reduced default for browser tests
        this.seedData = options.seedData || false;
        this.baseUrl = `http://localhost:${this.port}`;
        this.browser = null;
        this.page = null;
    }

    async runTests() {
        console.log('🚀 Starting React Webapp Performance Tests');
        console.log('='.repeat(60));
        console.log(`Port: ${this.port}, Iterations: ${this.iterations}, Seed Data: ${this.seedData}`);
        console.log('');

        const results = {
            timestamp: new Date().toISOString(),
            config: {
                port: this.port,
                iterations: this.iterations,
                seedData: this.seedData
            },
            tests: []
        };

        try {
            // Seed test data if requested
            if (this.seedData) {
                await this.seedTestData();
            }

            // Initialize browser
            await this.initBrowser();

            // Test 1: Home page load performance
            const homePageTest = await this.testHomePageLoad();
            results.tests.push(homePageTest);

            // Test 2: Filtering performance with various filter combinations
            const filterTest = await this.testFilteringPerformance();
            results.tests.push(filterTest);

            // Test 3: Search performance
            const searchTest = await this.testSearchPerformance();
            results.tests.push(searchTest);

            // Test 4: Sorting performance
            const sortTest = await this.testSortingPerformance();
            results.tests.push(sortTest);

            // Test 5: Bundle size analysis
            const bundleTest = await this.testBundleSize();
            results.tests.push(bundleTest);

        } catch (error) {
            console.error('❌ Performance test failed:', error.message);
            results.error = error.message;
        } finally {
            // Clean up browser
            await this.cleanupBrowser();
        }

        // Print summary
        this.printSummary(results);

        // Save results
        this.saveResults(results);

        return results;
    }

    async seedTestData() {
        console.log('🌱 Seeding test dog data...');

        try {
            // Change to the ETL directory and run the test script
            const etlDir = path.join(__dirname, '../../etl-scraper-py');
            const command = `cd ${etlDir} && python test_pipeline_5_dogs.py --limit 10 --live`;

            console.log('Running ETL to seed test data...');
            execSync(command, { stdio: 'inherit' });

            // Wait a moment for data to be written
            await this.delay(2000);
            console.log('✅ Test data seeded successfully');
        } catch (error) {
            console.error('❌ Failed to seed test data:', error.message);
            throw error;
        }
    }

    async initBrowser() {
        console.log('🌐 Initializing browser...');
        this.browser = await chromium.launch();
        this.page = await this.browser.newPage();

        // Set up performance monitoring
        await this.page.setViewportSize({ width: 1280, height: 720 });

        console.log('✅ Browser initialized');
    }

    async cleanupBrowser() {
        if (this.page) {
            await this.page.close();
        }
        if (this.browser) {
            await this.browser.close();
        }
    }

    async testHomePageLoad() {
        console.log('🏠 Testing Home page load performance...');

        const results = {
            name: 'Home Page Load Performance',
            measurements: []
        };

        for (let i = 0; i < this.iterations; i++) {
            console.log(`  Run ${i + 1}/${this.iterations}...`);

            try {
                // Start performance measurement
                const startTime = Date.now();

                // Navigate to home page
                await this.page.goto(this.baseUrl, { waitUntil: 'networkidle' });

                // Wait for the main content to load (dog cards or empty state)
                await this.page.waitForSelector('.dogs-grid, .empty-state', { timeout: 10000 });

                const loadTime = Date.now() - startTime;

                // Check if dogs loaded
                const dogCount = await this.page.locator('.dog-card').count();
                const hasAuth = await this.page.locator('[data-testid="status"]').isVisible();

                results.measurements.push({
                    duration: loadTime,
                    dogCount,
                    hasAuth,
                    success: true
                });

                console.log(`    ✅ Load time: ${loadTime}ms, Dogs: ${dogCount}, Auth: ${hasAuth}`);

            } catch (error) {
                console.log(`    ❌ Failed - ${error.message}`);
                results.measurements.push({
                    duration: null,
                    dogCount: 0,
                    hasAuth: false,
                    success: false,
                    error: error.message
                });
            }

            await this.delay(500);
        }

        const successfulMeasurements = results.measurements.filter(m => m.success);
        if (successfulMeasurements.length > 0) {
            results.average = this.calculateAverage(successfulMeasurements.map(m => m.duration));
            results.min = Math.min(...successfulMeasurements.map(m => m.duration));
            results.max = Math.max(...successfulMeasurements.map(m => m.duration));
            results.avgDogCount = this.calculateAverage(successfulMeasurements.map(m => m.dogCount));
        }

        return results;
    }

    async testFilteringPerformance() {
        console.log('🔍 Testing filtering performance...');

        const results = {
            name: 'Filtering Performance',
            measurements: []
        };

        // Define filter combinations to test
        const filterScenarios = [
            { name: 'No filters', filters: {} },
            { name: 'Available only', filters: { availability: ['available'] } },
            { name: 'Small size', filters: { sizes: ['Small'] } },
            { name: 'Multiple sizes', filters: { sizes: ['Small', 'Medium'] } },
            { name: 'Complex filter', filters: { availability: ['available'], sizes: ['Medium'], caseManagers: [] } }
        ];

        for (const scenario of filterScenarios) {
            console.log(`  Testing scenario: ${scenario.name}`);

            const scenarioResults = {
                scenario: scenario.name,
                measurements: []
            };

            for (let i = 0; i < this.iterations; i++) {
                try {
                    // Navigate to home page
                    await this.page.goto(this.baseUrl, { waitUntil: 'networkidle' });
                    await this.page.waitForSelector('.dogs-grid, .empty-state', { timeout: 5000 });

                    const startTime = Date.now();

                    // Apply filters by interacting with the filter drawer
                    if (Object.keys(scenario.filters).length > 0) {
                        await this.page.click('[data-testid="filter-button"]');
                        await this.page.waitForSelector('.filter-drawer', { timeout: 2000 });

                        // Apply the specific filters
                        await this.applyFilters(scenario.filters);

                        // Close filter drawer
                        await this.page.click('[data-testid="close-filter-drawer"]');
                    }

                    // Wait for filtering to complete
                    await this.page.waitForSelector('.dogs-grid, .empty-state', { timeout: 3000 });
                    await this.delay(100); // Brief pause for UI updates

                    const filterTime = Date.now() - startTime;
                    const visibleDogCount = await this.page.locator('.dog-card').count();
                    const activeFilterCount = await this.getActiveFilterCount();

                    scenarioResults.measurements.push({
                        duration: filterTime,
                        visibleDogs: visibleDogCount,
                        activeFilters: activeFilterCount,
                        success: true
                    });

                    console.log(`    ✅ ${filterTime}ms, ${visibleDogCount} dogs, ${activeFilterCount} filters`);

                } catch (error) {
                    console.log(`    ❌ Failed - ${error.message}`);
                    scenarioResults.measurements.push({
                        duration: null,
                        visibleDogs: 0,
                        activeFilters: 0,
                        success: false,
                        error: error.message
                    });
                }

                await this.delay(300);
            }

            const successfulMeasurements = scenarioResults.measurements.filter(m => m.success);
            if (successfulMeasurements.length > 0) {
                scenarioResults.average = this.calculateAverage(successfulMeasurements.map(m => m.duration));
                scenarioResults.avgVisibleDogs = this.calculateAverage(successfulMeasurements.map(m => m.visibleDogs));
            }

            results.measurements.push(scenarioResults);
        }

        return results;
    }

    async applyFilters(filterConfig) {
        // Apply availability filters
        if (filterConfig.availability) {
            for (const availability of filterConfig.availability) {
                const selector = `[data-testid="availability-${availability}"]`;
                await this.page.check(selector);
            }
        }

        // Apply size filters
        if (filterConfig.sizes) {
            for (const size of filterConfig.sizes) {
                const selector = `[data-testid="size-${size}"]`;
                await this.page.check(selector);
            }
        }

        // Apply case manager filters
        if (filterConfig.caseManagers && filterConfig.caseManagers.length > 0) {
            for (const manager of filterConfig.caseManagers) {
                const selector = `[data-testid="case-manager-${manager}"]`;
                await this.page.check(selector);
            }
        }
    }

    async getActiveFilterCount() {
        try {
            const badgeElement = await this.page.locator('.badge').first();
            const badgeText = await badgeElement.textContent();
            return parseInt(badgeText) || 0;
        } catch (error) {
            return 0;
        }
    }

    async testSearchPerformance() {
        console.log('🔎 Testing search performance...');

        const results = {
            name: 'Search Performance',
            measurements: []
        };

        // Test different search queries
        const searchQueries = [
            { query: '', description: 'Empty search (show all)' },
            { query: 'Max', description: 'Single name search' },
            { query: 'Golden', description: 'Breed search' },
            { query: 'Alice', description: 'Case manager search' }
        ];

        for (const searchTest of searchQueries) {
            console.log(`  Testing search: "${searchTest.query}" - ${searchTest.description}`);

            const searchResults = {
                query: searchTest.query,
                description: searchTest.description,
                measurements: []
            };

            for (let i = 0; i < this.iterations; i++) {
                try {
                    // Navigate to home page
                    await this.page.goto(this.baseUrl, { waitUntil: 'networkidle' });
                    await this.page.waitForSelector('.dogs-grid, .empty-state', { timeout: 5000 });

                    const startTime = Date.now();

                    // Perform search
                    const searchInput = await this.page.locator('.search-input');
                    await searchInput.fill(searchTest.query);

                    // Wait for search results to update
                    await this.page.waitForSelector('.dogs-grid, .empty-state', { timeout: 2000 });
                    await this.delay(200); // Brief pause for search to complete

                    const searchTime = Date.now() - startTime;
                    const resultCount = await this.page.locator('.dog-card').count();

                    searchResults.measurements.push({
                        duration: searchTime,
                        resultCount,
                        success: true
                    });

                    console.log(`    ✅ ${searchTime}ms, ${resultCount} results`);

                } catch (error) {
                    console.log(`    ❌ Failed - ${error.message}`);
                    searchResults.measurements.push({
                        duration: null,
                        resultCount: 0,
                        success: false,
                        error: error.message
                    });
                }

                await this.delay(300);
            }

            const successfulMeasurements = searchResults.measurements.filter(m => m.success);
            if (successfulMeasurements.length > 0) {
                searchResults.average = this.calculateAverage(successfulMeasurements.map(m => m.duration));
                searchResults.avgResultCount = this.calculateAverage(successfulMeasurements.map(m => m.resultCount));
            }

            results.measurements.push(searchResults);
        }

        return results;
    }

    async testSortingPerformance() {
        console.log('📊 Testing sorting performance...');

        const results = {
            name: 'Sorting Performance',
            measurements: []
        };

        // Test different sort options
        const sortOptions = [
            { field: 'Name', direction: 'asc', description: 'Name A-Z' },
            { field: 'Name', direction: 'desc', description: 'Name Z-A' },
            { field: 'Age', direction: 'asc', description: 'Age ascending' },
            { field: 'Age', direction: 'desc', description: 'Age descending' }
        ];

        for (const sortOption of sortOptions) {
            console.log(`  Testing sort: ${sortOption.description}`);

            const sortResults = {
                sortField: sortOption.field,
                sortDirection: sortOption.direction,
                description: sortOption.description,
                measurements: []
            };

            for (let i = 0; i < this.iterations; i++) {
                try {
                    // Navigate to home page
                    await this.page.goto(this.baseUrl, { waitUntil: 'networkidle' });
                    await this.page.waitForSelector('.dogs-grid, .empty-state', { timeout: 5000 });

                    const startTime = Date.now();

                    // Open sort menu and select option
                    await this.page.click('[data-testid="sort-button"]');
                    await this.page.waitForSelector('.sort-menu', { timeout: 2000 });

                    // Click the specific sort option
                    const sortSelector = `[data-testid="sort-${sortOption.field.toLowerCase()}-${sortOption.direction}"]`;
                    await this.page.click(sortSelector);

                    // Wait for sorting to complete
                    await this.page.waitForSelector('.dogs-grid, .empty-state', { timeout: 2000 });
                    await this.delay(200); // Brief pause for sorting to complete

                    const sortTime = Date.now() - startTime;
                    const dogCount = await this.page.locator('.dog-card').count();

                    sortResults.measurements.push({
                        duration: sortTime,
                        dogCount,
                        success: true
                    });

                    console.log(`    ✅ ${sortTime}ms, ${dogCount} dogs sorted`);

                } catch (error) {
                    console.log(`    ❌ Failed - ${error.message}`);
                    sortResults.measurements.push({
                        duration: null,
                        dogCount: 0,
                        success: false,
                        error: error.message
                    });
                }

                await this.delay(300);
            }

            const successfulMeasurements = sortResults.measurements.filter(m => m.success);
            if (successfulMeasurements.length > 0) {
                sortResults.average = this.calculateAverage(successfulMeasurements.map(m => m.duration));
                sortResults.avgDogCount = this.calculateAverage(successfulMeasurements.map(m => m.dogCount));
            }

            results.measurements.push(sortResults);
        }

        return results;
    }

    async testBundleSize() {
        console.log('📦 Analyzing bundle size...');

        const results = {
            name: 'Bundle Size Analysis',
            measurements: []
        };

        try {
            const distPath = path.join(__dirname, '../dist');

            if (fs.existsSync(distPath)) {
                const stats = fs.statSync(path.join(distPath, 'index.html'));
                results.bundleExists = true;
                results.buildSize = this.getDirectorySize(distPath);
                console.log(`  Build size: ${(results.buildSize / 1024).toFixed(2)} KB`);
            } else {
                results.bundleExists = false;
                console.log('  No build directory found - run `npm run build` first');
            }
        } catch (error) {
            console.log(`  Bundle analysis failed: ${error.message}`);
            results.error = error.message;
        }

        return results;
    }



    calculateAverage(numbers) {
        if (numbers.length === 0) return 0;
        return numbers.reduce((sum, num) => sum + num, 0) / numbers.length;
    }

    getDirectorySize(dirPath) {
        let totalSize = 0;

        function calculateSize(itemPath) {
            const stats = fs.statSync(itemPath);

            if (stats.isDirectory()) {
                const items = fs.readdirSync(itemPath);
                items.forEach(item => {
                    calculateSize(path.join(itemPath, item));
                });
            } else {
                totalSize += stats.size;
            }
        }

        calculateSize(dirPath);
        return totalSize;
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    printSummary(results) {
        console.log('\n' + '='.repeat(60));
        console.log('PERFORMANCE TEST SUMMARY');
        console.log('='.repeat(60));

        results.tests.forEach(test => {
            console.log(`\n${test.name}:`);

            if (test.average !== undefined) {
                console.log(`  Average: ${test.average.toFixed(2)}ms`);
                if (test.min !== undefined && test.max !== undefined) {
                    console.log(`  Min: ${test.min.toFixed(2)}ms`);
                    console.log(`  Max: ${test.max.toFixed(2)}ms`);
                }
                if (test.avgDogCount !== undefined) {
                    console.log(`  Avg Dogs Loaded: ${test.avgDogCount.toFixed(1)}`);
                }
            } else if (test.measurements && test.measurements.length > 0) {
                // Handle nested measurements (filtering, searching, sorting scenarios)
                test.measurements.forEach(measurement => {
                    if (measurement.scenario) {
                        console.log(`  ${measurement.scenario}:`);
                        if (measurement.average) {
                            console.log(`    Average: ${measurement.average.toFixed(2)}ms`);
                            console.log(`    Avg Visible Dogs: ${measurement.avgVisibleDogs?.toFixed(1) || 'N/A'}`);
                        }
                    } else if (measurement.query !== undefined) {
                        console.log(`  "${measurement.query}" - ${measurement.description}:`);
                        if (measurement.average) {
                            console.log(`    Average: ${measurement.average.toFixed(2)}ms`);
                            console.log(`    Avg Results: ${measurement.avgResultCount?.toFixed(1) || 'N/A'}`);
                        }
                    } else if (measurement.sortField) {
                        console.log(`  ${measurement.description}:`);
                        if (measurement.average) {
                            console.log(`    Average: ${measurement.average.toFixed(2)}ms`);
                            console.log(`    Avg Dogs Sorted: ${measurement.avgDogCount?.toFixed(1) || 'N/A'}`);
                        }
                    }
                });
            } else if (test.status) {
                console.log(`  ${test.status}`);
            } else if (test.buildSize) {
                console.log(`  Build size: ${(test.buildSize / 1024).toFixed(2)} KB`);
            } else if (test.bundleExists === false) {
                console.log('  No build directory found - run `npm run build` first');
            }
        });

        console.log('\n✅ Performance testing completed');
        console.log('\n💡 Tips for optimization:');
        console.log('   - Home page load times should be under 2 seconds');
        console.log('   - Filtering operations should complete under 500ms');
        console.log('   - Search should respond within 300ms');
        console.log('   - Sorting should complete within 200ms');
        console.log('   - Run `npm run build` to analyze production bundle size');
    }

    saveResults(results) {
        const filename = `performance_results_${Date.now()}.json`;
        const filepath = path.join(__dirname, filename);

        try {
            fs.writeFileSync(filepath, JSON.stringify(results, null, 2));
            console.log(`📄 Results saved to: ${filename}`);
        } catch (error) {
            console.error('❌ Failed to save results:', error.message);
        }
    }
}

// Check if dev server is running
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

// Main execution
async function main() {
    // Safety check for development environment
    if (process.env.NODE_ENV === 'production') {
        console.error('❌ PRODUCTION SAFETY CHECK FAILED ❌');
        console.error('Performance tests should never run in production environment.');
        console.error('This script is for development/testing only.');
        process.exit(1);
    }

    // Additional check for production-looking URLs
    const port = process.env.PORT || 5173;
    if (port !== 5173 && port !== 3000) {
        console.warn('⚠️  WARNING: Using non-standard port. Ensure this is a dev server.');
    }

    const args = process.argv.slice(2);
    const options = {};

    // Parse command line arguments
    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--port':
                options.port = parseInt(args[++i]);
                break;
            case '--iterations':
                options.iterations = parseInt(args[++i]);
                break;
            case '--seed-data':
                options.seedData = true;
                break;
            default:
                if (args[i].startsWith('--')) {
                    console.error(`Unknown option: ${args[i]}`);
                    process.exit(1);
                }
        }
    }

    const tester = new PerformanceTester(options);

    // Check if dev server is running
    const serverRunning = await checkDevServer(tester.port);

    if (!serverRunning) {
        console.log(`❌ Dev server not running on port ${tester.port}`);
        console.log('💡 Start the dev server first:');
        console.log('   cd services/webapp-react && npm run dev');
        process.exit(1);
    }

    await tester.runTests();
}

// Run if called directly
if (require.main === module) {
    main().catch(console.error);
}

module.exports = { PerformanceTester };

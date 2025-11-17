/**
 * Performance test execution engine.
 * Runs scenarios, collects measurements, coordinates browser actions.
 */

const { chromium } = require('playwright');
const { calculateAverage } = require('./reporters');

/**
 * Performance test runner.
 * Executes scenarios and collects measurements.
 */
class PerformanceTester {
    constructor(options = {}) {
        this.port = options.port || 5173;
        this.jsonOnly = options.jsonOnly || false;
        this.scenarios = options.scenarios || {};
        this.baseUrl = `http://localhost:${this.port}`;
        this.browser = null;
        this.page = null;
    }

    async runScenarios() {
        if (!this.jsonOnly) {
            console.log('🚀 Starting Data-Driven Performance Tests');
            console.log('='.repeat(60));
            console.log(`Port: ${this.port}, Scenarios: ${Object.keys(this.scenarios).length}`);
            console.log('');
        }

        const results = {
            timestamp: new Date().toISOString(),
            config: {
                port: this.port,
                scenarios: Object.keys(this.scenarios)
            },
            results: {}
        };

        try {
            await this.initBrowser();

            for (const [scenarioKey, scenarioConfig] of Object.entries(this.scenarios)) {
                if (!this.jsonOnly) {
                    console.log(`📊 Running scenario: ${scenarioConfig.name}`);
                }

                const scenarioResult = await this.runScenario(scenarioKey, scenarioConfig);
                results.results[scenarioKey] = scenarioResult;
            }

        } catch (error) {
            if (!this.jsonOnly) {
                console.error('❌ Performance test failed:', error.message);
            }
            results.error = error.message;
        } finally {
            await this.cleanupBrowser();
        }

        return results;
    }

    async runScenario(scenarioKey, scenarioConfig) {
        const result = {
            name: scenarioConfig.name,
            description: scenarioConfig.description,
            measurements: []
        };

        const iterations = scenarioConfig.iterations || 1;

        if (scenarioConfig.scenarios) {
            // Multi-scenario test (e.g., filtering with different combinations)
            for (const subScenario of scenarioConfig.scenarios) {
                const subResult = await this.runSubScenario(scenarioConfig, subScenario, iterations);
                result.measurements.push(subResult);
            }
        } else {
            // Single scenario test
            const measurements = await this.runScenarioActions(scenarioConfig, {}, iterations);
            result.measurements = measurements;
        }

        return result;
    }

    async runSubScenario(scenarioConfig, subScenario, iterations) {
        const subResult = {
            scenario: subScenario.name || subScenario.description,
            ...subScenario,
            measurements: []
        };

        const measurements = await this.runScenarioActions(scenarioConfig, subScenario, iterations);
        subResult.measurements = measurements;

        // Calculate averages
        const successful = measurements.filter(m => m.success);
        if (successful.length > 0) {
            subResult.average = calculateAverage(successful.map(m => m.duration));
            subResult.successRate = (successful.length / measurements.length) * 100;
        }

        return subResult;
    }

    async runScenarioActions(scenarioConfig, context, iterations) {
        const measurements = [];

        for (let i = 0; i < iterations; i++) {
            const startTime = Date.now();
            const measurement = { iteration: i + 1 };

            try {
                for (const action of scenarioConfig.actions) {
                    await this.executeAction(action, { ...context, measurement });
                }

                measurement.duration = Date.now() - startTime;
                measurement.success = true;

                // Add configured measurements
                if (scenarioConfig.measurements) {
                    for (const metric of scenarioConfig.measurements) {
                        measurement[metric] = await this.getMeasurement(metric);
                    }
                }

            } catch (error) {
                measurement.duration = Date.now() - startTime;
                measurement.success = false;
                measurement.error = error.message;
            }

            measurements.push(measurement);
            await this.delay(300); // Brief pause between iterations
        }

        return measurements;
    }

    async executeAction(action, context) {
        const processedAction = this.processTemplate(action, context);

        switch (processedAction.type) {
            case 'navigate':
                await this.page.goto(this.baseUrl + processedAction.url, {
                    waitUntil: processedAction.waitFor || 'load'
                });
                break;

            case 'waitForSelector':
                await this.page.waitForSelector(processedAction.selector, {
                    timeout: processedAction.timeout || 5000
                });
                break;

            case 'click':
                await this.page.click(processedAction.selector);
                break;

            case 'type':
                await this.page.fill(processedAction.selector, processedAction.text);
                break;

            case 'applyFilters':
                await this.applyFilters(processedAction.filters);
                break;

            case 'search':
                await this.performSearch(processedAction.query);
                break;

            default:
                throw new Error(`Unknown action type: ${processedAction.type}`);
        }
    }

    processTemplate(obj, context) {
        if (typeof obj === 'string') {
            return obj.replace(/\{\{(\w+)\.(\w+)\}\}/g, (match, objName, propName) => {
                return context[objName]?.[propName] || match;
            });
        } else if (Array.isArray(obj)) {
            return obj.map(item => this.processTemplate(item, context));
        } else if (obj && typeof obj === 'object') {
            const result = {};
            for (const [key, value] of Object.entries(obj)) {
                result[key] = this.processTemplate(value, context);
            }
            return result;
        }
        return obj;
    }

    async getMeasurement(metric) {
        switch (metric) {
            case 'loadTime':
                return Date.now() - this.page.metrics?.Timestamp || 0;
            case 'dogCount':
                return await this.page.locator('.dog-card').count();
            case 'authStatus':
                return await this.page.locator('[data-testid="status"]').isVisible();
            case 'visibleDogs':
                return await this.page.locator('.dog-card').count();
            case 'activeFilters':
                return await this.getActiveFilterCount();
            case 'resultCount':
                return await this.page.locator('.dog-card').count();
            default:
                return null;
        }
    }

    async initBrowser() {
        if (!this.jsonOnly) {
            console.log('🌐 Initializing browser...');
        }
        this.browser = await chromium.launch();
        this.page = await this.browser.newPage();
        await this.page.setViewportSize({ width: 1280, height: 720 });
        if (!this.jsonOnly) {
            console.log('✅ Browser initialized');
        }
    }

    async cleanupBrowser() {
        if (this.page) {
            await this.page.close();
        }
        if (this.browser) {
            await this.browser.close();
        }
    }

    async applyFilters(filterConfig) {
        // Open filter drawer
        await this.page.click('[data-testid="filter-button"]');
        await this.page.waitForSelector('.filter-drawer', { timeout: 2000 });

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

        // Close filter drawer
        await this.page.click('[data-testid="close-filter-drawer"]');
        await this.page.waitForSelector('.dogs-grid, .empty-state', { timeout: 3000 });
        await this.delay(100);
    }

    async performSearch(query) {
        const searchInput = await this.page.locator('.search-input');
        await searchInput.fill(query);
        await this.page.waitForSelector('.dogs-grid, .empty-state', { timeout: 2000 });
        await this.delay(200);
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

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

module.exports = { PerformanceTester };


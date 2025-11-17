/**
 * Pure functions for building test commands.
 * Table-driven: commands defined as data, not branching logic.
 * No side effects, no execution - just command construction.
 */

const { WEB_ENV_VARS } = require('./firebaseEnvVars');

/**
 * Table-driven test command definitions.
 * Each entry defines: name, default command, cwd, envVar override name, and env builder.
 */
const TEST_COMMANDS = [
  {
    name: 'webapp',
    defaultCmd: 'npm test -- --run --reporter=json',
    cwd: 'services/webapp-react',
    envVar: 'WEBAPP_TEST_CMD',
    buildEnv: (baseEnv) => {
      const env = { ...baseEnv };
      // Use shared env var list from firebaseEnvVars
      for (const varName of WEB_ENV_VARS) {
        const vitePrefixed = `VITE_${varName}`;
        const value = env[varName] || env[vitePrefixed] || 'test-value';
        if (!env[varName]) env[varName] = value;
        if (!env[vitePrefixed]) env[vitePrefixed] = value;
      }
      return env;
    }
  },
  {
    name: 'etl',
    defaultCmd: 'python3 -m pytest tests/ --tb=line -q',
    cwd: 'services/etl_scraper_py',
    envVar: 'ETL_TEST_CMD',
    buildEnv: (baseEnv) => ({ ...baseEnv })
  },
  {
    name: 'webapp-e2e',
    defaultCmd: 'npm run test:e2e -- --grep "auth" --reporter=list',
    cwd: 'services/webapp-react',
    envVar: 'E2E_TEST_CMD',
    buildEnv: (baseEnv) => ({ ...baseEnv })
  },
  {
    name: 'etl-e2e',
    defaultCmd: './tests/e2e/run_e2e_tests.sh',
    cwd: 'services/etl_scraper_py',
    envVar: 'ETL_E2E_TEST_CMD',
    buildEnv: (baseEnv) => ({ ...baseEnv, E2E_LIVE_DB: '1' })
  }
];

/**
 * Build a test command from table-driven definition.
 * @param {Object} def - Command definition from TEST_COMMANDS table
 * @param {Object} options - Command options
 * @param {string} options.cwd - Working directory override
 * @returns {Object} Command configuration
 */
function buildCommandFromDef(def, options = {}) {
  const cwd = options.cwd || def.cwd;
  const command = process.env[def.envVar] || def.defaultCmd;
  const env = def.buildEnv(process.env);

  return {
    command,
    options: {
      encoding: 'utf8',
      maxBuffer: 1024 * 1024 * 10,
      cwd,
      env
    },
    service: def.name
  };
}

/**
 * Build webapp test command.
 * @param {Object} options - Command options
 * @param {string} options.cwd - Working directory override
 * @returns {Object} Command configuration
 */
function buildWebappTestCommand(options = {}) {
  const def = TEST_COMMANDS.find(cmd => cmd.name === 'webapp');
  return buildCommandFromDef(def, options);
}

/**
 * Build ETL test command.
 * @param {Object} options - Command options
 * @param {string} options.cwd - Working directory override
 * @returns {Object} Command configuration
 */
function buildEtlTestCommand(options = {}) {
  const def = TEST_COMMANDS.find(cmd => cmd.name === 'etl');
  return buildCommandFromDef(def, options);
}

/**
 * Build webapp E2E test command.
 * @param {Object} options - Command options
 * @param {string} options.cwd - Working directory override
 * @returns {Object} Command configuration
 */
function buildWebappE2eTestCommand(options = {}) {
  const def = TEST_COMMANDS.find(cmd => cmd.name === 'webapp-e2e');
  return buildCommandFromDef(def, options);
}

/**
 * Build ETL E2E test command.
 * @param {Object} options - Command options
 * @param {string} options.cwd - Working directory override
 * @returns {Object} Command configuration
 */
function buildEtlE2eTestCommand(options = {}) {
  const def = TEST_COMMANDS.find(cmd => cmd.name === 'etl-e2e');
  return buildCommandFromDef(def, options);
}

module.exports = {
  TEST_COMMANDS,
  buildWebappTestCommand,
  buildEtlTestCommand,
  buildWebappE2eTestCommand,
  buildEtlE2eTestCommand
};

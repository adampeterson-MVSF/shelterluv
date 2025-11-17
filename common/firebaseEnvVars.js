/**
 * Pure configuration module for environment variable specifications.
 * Single source of truth for env var names per profile.
 * 
 * IMPORTANT: common/config.json (via configData) is the ONLY place where per-profile env var lists live.
 * Never duplicate env var lists elsewhere - always import from this module.
 * 
 * This module is pure configuration - no validation logic (that's in firebaseConfig.js).
 */

const { getEnvProfiles } = require('./configData');

const makeFrozenArray = (items) => Object.freeze([...items]);

// Convert config data to frozen structure
const envProfilesData = getEnvProfiles();
const ENV_PROFILES = Object.freeze(
  Object.fromEntries(
    Object.entries(envProfilesData).map(([key, value]) => [
      key,
      Object.freeze({
        required: makeFrozenArray(value.required),
        optional: makeFrozenArray(value.optional)
      })
    ])
  )
);

const WEB_ENV_VARS = ENV_PROFILES.web.required;
const ADMIN_ENV_VARS = ENV_PROFILES.admin.required;
const ETL_ENV_VARS = ENV_PROFILES.etl.required;
const DEV_ENV_VARS = ENV_PROFILES.dev.required;

// Mapping of profile -> env var that contains the project ID
const PROJECT_ID_ENV_VARS = {
  admin: 'FIREBASE_PROJECT_ID',
  etl: 'GCP_PROJECT'
};

function getProfileEnvSpec(profile) {
  const spec = ENV_PROFILES[profile];
  if (!spec) {
    throw new Error(`Unknown profile: ${profile}. Use 'web', 'admin', 'etl', or 'dev'`);
  }
  return spec;
}

function getProjectIdEnvVar(profile) {
  const envVar = PROJECT_ID_ENV_VARS[profile];
  if (!envVar) {
    throw new Error(`Profile '${profile}' does not have a project ID environment variable`);
  }
  return envVar;
}

/**
 * Collect environment variables for a specific profile.
 * @param {string} profile - profile key
 * @param {NodeJS.ProcessEnv} [envSource] - source object for env lookup (defaults to process.env)
 * @returns {{required: readonly string[], optional: readonly string[], values: Record<string, string | undefined>, missing: string[], isValid: boolean}}
 */
function collectProfileEnv(profile, envSource = process.env) {
  const spec = getProfileEnvSpec(profile);
  const values = {};

  for (const name of [...spec.required, ...spec.optional]) {
    values[name] = envSource[name];
  }

  const missing = spec.required.filter((varName) => !envSource[varName]);

  return {
    required: spec.required,
    optional: spec.optional,
    values,
    missing,
    isValid: missing.length === 0
  };
}

/**
 * Validate environment variables for a specific profile.
 * @param {string} profile - 'web', 'admin', 'etl', or 'dev'
 * @param {NodeJS.ProcessEnv} [envSource] - source object for env lookup (defaults to process.env)
 * @returns {{required: string[], optional: string[], missing: string[], isValid: boolean}}
 */
function validateEnv(profile, envSource = process.env) {
  const { required, optional, missing, isValid } = collectProfileEnv(profile, envSource);
  return {
    required,
    optional,
    missing,
    isValid
  };
}

/**
 * Get a frozen view of the environment profiles specification.
 * Prevents accidental mutation of ENV_PROFILES.
 * @returns {Object} Frozen copy of ENV_PROFILES
 */
function getFrozenEnvProfiles() {
  return Object.freeze({ ...ENV_PROFILES });
}

/**
 * Export structured env spec for Python consumption.
 * Returns a JSON-serializable object that Python config_loader.py can read.
 * @returns {Object} Structured env spec with required/optional vars per profile
 */
function getStructuredEnvSpec() {
  return {
    profiles: ENV_PROFILES,
    projectIdEnvVars: PROJECT_ID_ENV_VARS
  };
}

module.exports = {
  ENV_PROFILES,
  WEB_ENV_VARS,
  ADMIN_ENV_VARS,
  ETL_ENV_VARS,
  DEV_ENV_VARS,
  PROJECT_ID_ENV_VARS,
  getProfileEnvSpec,
  getProjectIdEnvVar,
  collectProfileEnv,
  validateEnv,
  getFrozenEnvProfiles,
  getStructuredEnvSpec
};

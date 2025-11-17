/**
 * Centralized Firebase configuration using profile-based approach.
 * Single source for all Firebase environment variable handling.
 */

const {
  getProfileEnvSpec,
  validateEnv,
  getProjectIdEnvVar
} = require('./firebaseEnvVars');

const ENV_TO_CONFIG_MAP = {
  FIREBASE_API_KEY: 'apiKey',
  FIREBASE_AUTH_DOMAIN: 'authDomain',
  FIREBASE_PROJECT_ID: 'projectId',
  FIREBASE_STORAGE_BUCKET: 'storageBucket',
  FIREBASE_MESSAGING_SENDER_ID: 'messagingSenderId',
  FIREBASE_APP_ID: 'appId'
};

function requireEnvVar(name, env) {
  const value = env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

/**
 * Ensure all required environment variables are present for a given profile.
 * @param {string} profile - 'web', 'admin', or 'etl'
 * @param {NodeJS.ProcessEnv} [env] - environment source
 * @throws {Error} If any required env vars are missing
 */
function ensureProfile(profile, env = process.env) {
  const validation = validateEnv(profile, env);
  if (!validation.isValid) {
    throw new Error(`Missing required environment variables for ${profile} profile: ${validation.missing.join(', ')}`);
  }
  return validation;
}

/**
 * Get Firebase project ID from environment variables.
 * Uses the appropriate env var for the given profile.
 * @param {string} profile - 'admin' or 'etl'
 * @param {NodeJS.ProcessEnv} [env] - environment source
 * @returns {string} Project ID
 * @throws {Error} If project ID env var is not set or profile doesn't have one
 */
function getProjectId(profile, env = process.env) {
  const projectIdEnvVar = getProjectIdEnvVar(profile);
  return requireEnvVar(projectIdEnvVar, env);
}

/**
 * Get Firebase configuration for webapp from environment variables.
 * Used only by webapp build/runtime (not admin scripts).
 * @param {Function} getEnv - Function to get environment variables (expects bare names, adds VITE_ prefix)
 * @param {NodeJS.ProcessEnv|Object} [env] - environment source for validation (defaults to process.env)
 * @returns {Object} Firebase config object with validated env vars
 * @throws {Error} If any required FIREBASE_* variables are missing
 */
function getWebFirebaseConfigFromEnv(getEnv, env = process.env) {
  // Validate that required env vars are conceptually present (don't check values in browser)
  ensureProfile('web', env);

  if (!getEnv) {
    throw new Error('getEnv function is required for webapp Firebase config');
  }

  const config = {};
  const missing = [];
  const { required } = getProfileEnvSpec('web');

  for (const envVar of required) {
    // envVar is bare name like 'FIREBASE_API_KEY'
    // getEnv function adds VITE_ prefix internally
    const value = getEnv(envVar);
    if (!value) {
      missing.push(envVar);
      continue;
    }

    const configKey = ENV_TO_CONFIG_MAP[envVar];
    if (!configKey) {
      throw new Error(`Unknown Firebase environment variable: ${envVar}`);
    }
    config[configKey] = value;
  }

  if (missing.length > 0) {
    throw new Error(`Missing required environment variables for web profile: ${missing.join(', ')}`);
  }

  return config;
}

/**
 * Get Firebase project ID for admin operations.
 * @param {NodeJS.ProcessEnv} [env] - Environment source (defaults to process.env)
 * @returns {string} Project ID
 * @throws {Error} If FIREBASE_PROJECT_ID is not set
 */
function getAdminProjectId(env = process.env) {
  return getProjectId('admin', env);
}

/**
 * Get Firebase project ID for ETL operations.
 * @param {NodeJS.ProcessEnv} [env] - Environment source (defaults to process.env)
 * @returns {string} Project ID
 * @throws {Error} If GCP_PROJECT is not set
 */
function getEtlProjectId(env = process.env) {
  return getProjectId('etl', env);
}

module.exports = {
  ensureProfile,
  getProjectId,
  getAdminProjectId,
  getEtlProjectId,
  getWebFirebaseConfigFromEnv
};

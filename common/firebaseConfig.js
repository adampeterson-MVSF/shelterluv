/**
 * Centralized Firebase configuration for both webapp and admin scripts.
 * Provides separate functions for webapp (VITE_*) and admin (FIREBASE_*) configurations.
 */

const {
  REQUIRED_FIREBASE_WEB_ENV_VARS,
  REQUIRED_FIREBASE_ADMIN_ENV_VARS,
} = require('./firebaseEnvVars');

/**
 * Validate that all required Firebase admin environment variables are present.
 * Throws an Error if any are missing. No other side effects.
 * @throws {Error} If any required admin env vars are missing
 */
function validateFirebaseAdminEnv() {
  for (const envVar of REQUIRED_FIREBASE_ADMIN_ENV_VARS) {
    if (!process.env[envVar]) {
      throw new Error(`Missing required environment variable: ${envVar}`);
    }
  }
}

/**
 * Get Firebase project ID from environment variables.
 * Uses FIREBASE_PROJECT_ID for admin operations.
 * @returns {string} Project ID
 * @throws {Error} If FIREBASE_PROJECT_ID is not set
 */
function getFirebaseProjectId() {
  const projectId = process.env.FIREBASE_PROJECT_ID;
  if (!projectId) {
    throw new Error('Missing required environment variable: FIREBASE_PROJECT_ID');
  }
  return projectId;
}

/**
 * Initialize Firebase admin app with validated config.
 * Returns the initialized admin app instance.
 * @returns {Object} Initialized Firebase admin app
 */
function initializeFirebaseApp() {
  validateFirebaseAdminEnv();
  const admin = require('firebase-admin');
  const projectId = getFirebaseProjectId();

  return admin.initializeApp({
    projectId: projectId
  });
}

/**
 * Get Firebase configuration for webapp from VITE_ environment variables.
 * Throws on missing keys; no silent fallbacks.
 * Used only by webapp build/runtime (not admin scripts).
 * @param {Function} getEnv - Function to get environment variables (defaults to process.env)
 * @returns {Object} Firebase config object with VITE_ validated env vars
 * @throws {Error} If any required VITE_FIREBASE_* variables are missing
 */
function getWebFirebaseConfigFromEnv(getEnv = (k) => process.env[k]) {
  const config = {};

  for (const envVar of REQUIRED_FIREBASE_WEB_ENV_VARS) {
    const viteVar = `VITE_${envVar}`;
    const value = getEnv(viteVar);
    if (!value) {
      throw new Error(`Missing required environment variable: ${viteVar}`);
    }
    config[envVar.toLowerCase()] = value;
  }

  return config;
}

module.exports = {
  validateFirebaseAdminEnv,
  getFirebaseProjectId,
  initializeFirebaseApp,
  getWebFirebaseConfigFromEnv
};

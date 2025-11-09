/**
 * Centralized Firebase configuration for both webapp and admin scripts.
 * Provides separate functions for webapp (VITE_*) and admin (FIREBASE_*) configurations.
 */

const { REQUIRED_FIREBASE_ENV_VARS } = require('./firebaseEnvVars');

/**
 * Validate that all required Firebase admin environment variables are present.
 * Throws an Error if any are missing. No other side effects.
 * @throws {Error} If any required admin env vars are missing
 */
function validateFirebaseEnv() {
  for (const envVar of REQUIRED_FIREBASE_ADMIN_ENV_VARS) {
    if (!process.env[envVar]) {
      throw new Error(`Missing required environment variable: ${envVar}`);
    }
  }
}

/**
 * Get Firebase project ID from environment variables.
 * Uses FIREBASE_PROJECT_ID for admin operations.
 * @returns {string} Project ID or empty string if not set
 */
function getFirebaseProjectId() {
  return process.env.FIREBASE_PROJECT_ID || '';
}

/**
 * Initialize Firebase admin app with validated config.
 * Returns the initialized admin app instance.
 * @returns {Object} Initialized Firebase admin app
 */
function initializeFirebaseApp() {
  validateFirebaseEnv();
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
 * @returns {Object} Firebase config object with VITE_ validated env vars
 * @throws {Error} If any required VITE_FIREBASE_* variables are missing
 */
function getWebFirebaseConfig() {
  const config = {};

  for (const envVar of REQUIRED_FIREBASE_ENV_VARS) {
    const viteVar = `VITE_${envVar}`;
    const value = process.env[viteVar];
    if (!value) {
      throw new Error(`Missing required environment variable: ${viteVar}`);
    }
    config[envVar.toLowerCase()] = value;
  }

  return config;
}

module.exports = {
  validateFirebaseEnv,
  getFirebaseProjectId,
  initializeFirebaseApp,
  getWebFirebaseConfig
};

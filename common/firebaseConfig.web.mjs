/**
 * ES6 module Firebase config for webapp usage.
 * Pure browser-compatible implementation that doesn't use Node.js APIs.
 * Provides getWebFirebaseConfigFromEnv as ES6 export for Vite/React compatibility.
 */

// Mapping from environment variable names to Firebase config keys
const ENV_TO_CONFIG_MAP = {
  FIREBASE_API_KEY: 'apiKey',
  FIREBASE_AUTH_DOMAIN: 'authDomain',
  FIREBASE_PROJECT_ID: 'projectId',
  FIREBASE_STORAGE_BUCKET: 'storageBucket',
  FIREBASE_MESSAGING_SENDER_ID: 'messagingSenderId',
  FIREBASE_APP_ID: 'appId'
};

// Required Firebase environment variables for web profile
const WEB_REQUIRED_VARS = [
  'FIREBASE_API_KEY',
  'FIREBASE_AUTH_DOMAIN',
  'FIREBASE_PROJECT_ID',
  'FIREBASE_STORAGE_BUCKET',
  'FIREBASE_MESSAGING_SENDER_ID',
  'FIREBASE_APP_ID'
];

/**
 * Get Firebase configuration for webapp from environment variables.
 * Used only by webapp build/runtime (not admin scripts).
 * @param {Function} getEnv - Function to get environment variables (expects bare names, adds VITE_ prefix)
 * @returns {Object} Firebase config object with validated env vars
 * @throws {Error} If any required FIREBASE_* variables are missing
 */
export function getWebFirebaseConfigFromEnv(getEnv) {
  if (!getEnv) {
    throw new Error('getEnv function is required for webapp Firebase config');
  }

  const config = {};
  const missing = [];

  for (const envVar of WEB_REQUIRED_VARS) {
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

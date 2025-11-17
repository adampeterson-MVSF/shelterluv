/**
 * ES6 module re-export of Firebase config for webapp usage.
 * Provides getWebFirebaseConfigFromEnv as ES6 export for Vite/React compatibility.
 * This is now a thin wrapper around the main firebaseConfig.js module.
 */

// Dynamic import to avoid CommonJS/ES6 module issues
import { createRequire } from 'module';
const require = createRequire(import.meta.url);

// Import the main implementation from CommonJS module
const { getWebFirebaseConfigFromEnv } = require('./firebaseConfig.js');

// Re-export for ES6 compatibility
export { getWebFirebaseConfigFromEnv };

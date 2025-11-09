/**
 * Shared Firebase environment variable configuration.
 * Split into webapp (Vite/browser) and admin (Node scripts) requirements.
 */

// Environment variables required for webapp/browser Firebase usage (Vite)
// VITE_ prefix required for browser access in Vite applications
const REQUIRED_FIREBASE_WEB_ENV_VARS = [
  'FIREBASE_API_KEY',
  'FIREBASE_AUTH_DOMAIN',
  'FIREBASE_PROJECT_ID',
  'FIREBASE_STORAGE_BUCKET',
  'FIREBASE_MESSAGING_SENDER_ID',
  'FIREBASE_APP_ID'
];

// Environment variables required for admin/Node Firebase operations
const REQUIRED_FIREBASE_ADMIN_ENV_VARS = [
  'FIREBASE_PROJECT_ID'  // Core project identifier for admin operations
];

module.exports = {
  REQUIRED_FIREBASE_WEB_ENV_VARS,
  REQUIRED_FIREBASE_ADMIN_ENV_VARS,
  // Keep legacy export for backward compatibility
  REQUIRED_FIREBASE_ENV_VARS: REQUIRED_FIREBASE_WEB_ENV_VARS
};

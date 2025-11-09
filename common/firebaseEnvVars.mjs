/**
 * Shared Firebase environment variable configuration - ESM version.
 * Used by webapp to ensure consistency with Node scripts.
 * VITE_ prefix required for browser access in Vite applications.
 */

export const REQUIRED_FIREBASE_ENV_VARS = [
  'FIREBASE_API_KEY',
  'FIREBASE_AUTH_DOMAIN',
  'FIREBASE_PROJECT_ID',
  'FIREBASE_STORAGE_BUCKET',
  'FIREBASE_MESSAGING_SENDER_ID',
  'FIREBASE_APP_ID'
];

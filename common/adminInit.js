/**
 * Single entry for all Node admin usage.
 * Handles safety checks and Firebase Admin initialization.
 * Uses explicit project ID functions from firebaseConfig.
 */

const { createAdminApp } = require('./firebaseAdmin');
const { getProjectId } = require('./firebaseConfig');
const { assertDevScriptsEnabled, assertSafeProject } = require('./devScriptSafety');

/**
 * Initialize Firebase Admin with safety checks.
 * This is the ONLY place where firebase-admin gets initialized in scripts.
 *
 * @param {Object} options - Configuration options
 * @param {boolean} [options.requireDevScripts=true] - Whether to require DEV_SCRIPTS_ENABLED=1
 * @returns {Object} Initialized Firebase admin app
 * @throws {Error} If safety checks fail or initialization fails
 */
function initializeAdmin(options = {}) {
  const { requireDevScripts = true } = options;

  // Safety checks
  if (requireDevScripts) {
    assertDevScriptsEnabled();
  }
  const projectId = getProjectId('admin');
  assertSafeProject(projectId, { allowDestructive: true });

  // Initialize Firebase Admin
  return createAdminApp();
}

/**
 * Get the initialized Firebase Admin app instance.
 * Convenience function for scripts that need the app directly.
 *
 * @param {Object} options - Configuration options (same as initializeAdmin)
 * @returns {Object} Initialized Firebase admin app
 * @throws {Error} If safety checks fail or initialization fails
 */
function getAdminApp(options = {}) {
  return initializeAdmin(options);
}

/**
 * Initialize Firebase Admin and return the Firestore database instance.
 * Convenience function for scripts that just need the DB.
 *
 * @param {Object} options - Configuration options (same as initializeAdmin)
 * @returns {Object} Firestore database instance
 * @throws {Error} If safety checks fail or initialization fails
 */
function getAdminDb(options = {}) {
  const admin = initializeAdmin(options);
  return admin.firestore();
}

module.exports = {
  initializeAdmin,
  getAdminApp,
  getAdminDb
};

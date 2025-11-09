/**
 * Centralized safety checks for dev scripts.
 * Dead simple guards that all dev scripts should use.
 */

const { assertNotProdProject } = require('./firebaseSafetyConfig');
const { getFirebaseProjectId } = require('./firebaseConfig');

/**
 * Assert that we're using a safe project for destructive operations.
 * Use this at the start of scripts that delete or modify production data.
 * @throws {Error} If project is not safe for destructive operations
 */
function assertSafeForDestructiveOps() {
  if (process.env.DEV_SCRIPTS_ENABLED !== '1') {
    throw new Error('DEV_SCRIPTS_ENABLED=1 environment variable required');
  }
  const projectId = getFirebaseProjectId();
  assertNotProdProject(projectId, 'destructive operations'); // Uses centralized safety config
}

module.exports = {
  assertSafeForDestructiveOps
};

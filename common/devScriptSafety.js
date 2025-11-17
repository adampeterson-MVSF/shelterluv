/**
 * Simple safety checks for dev scripts.
 * Always throw - no ambiguity.
 * 
 * This module is the single source of truth for safe project validation.
 * All scripts must use isSafeProject() or assertSafeProject() - never hardcode project lists.
 */

const { getProjectId } = require('./firebaseConfig');
const { getProjectSafetyMap } = require('./configArtifact');

/**
 * Check if a project ID is safe for development operations.
 * Uses the project safety map as single source of truth.
 * @param {string} projectId - The Firebase project ID to check
 * @returns {boolean} True if the project is safe for dev operations
 */
function isSafeProject(projectId) {
  const projectMap = getProjectSafetyMap();
  return projectMap[projectId]?.is_safe || false;
}

/**
 * Assert that dev scripts are enabled.
 * @throws {Error} If DEV_SCRIPTS_ENABLED is not set to '1'
 */
function assertDevScriptsEnabled() {
  if (process.env.DEV_SCRIPTS_ENABLED !== '1') {
    throw new Error('DEV_SCRIPTS_ENABLED=1 environment variable required');
  }
}

/**
 * Assert that a project is safe for operations.
 * @param {string} projectId - The Firebase project ID to check
 * @param {Object} options - Safety options
 * @param {boolean} options.allowDestructive - Whether to allow destructive operations (default: false)
 * @throws {Error} If project is not safe or destructive operations not allowed
 */
function assertSafeProject(projectId, options = {}) {
  const { allowDestructive = false } = options;

  if (!isSafeProject(projectId)) {
    throw new Error(`Project "${projectId}" is not safe for development operations`);
  }

  if (!allowDestructive) {
    assertDevScriptsEnabled();
  }
}

/**
 * Assert that both dev scripts are enabled and project is safe for destructive operations.
 * Combines both checks into one convenient function for scripts.
 * @param {string} projectId - The Firebase project ID to check
 * @throws {Error} If either dev scripts are not enabled or project is not safe
 */
function assertSafeForDestructiveOps(projectId) {
  assertDevScriptsEnabled();
  assertSafeProject(projectId, { allowDestructive: true });
}

/**
 * Unified safety assertion API.
 * Single entry point for all safety checks.
 * @param {string} projectId - The Firebase project ID to check
 * @param {Object} options - Safety options
 * @param {boolean} options.allowDestructive - Whether this is a destructive operation (default: false)
 * @throws {Error} If operation is not safe
 */
function assertSafe(projectId, options = {}) {
  const { allowDestructive = false } = options;
  assertSafeProject(projectId, { allowDestructive });
}

module.exports = {
  isSafeProject,
  assertDevScriptsEnabled,
  assertSafeProject,
  assertSafeForDestructiveOps,
  assertSafe
};

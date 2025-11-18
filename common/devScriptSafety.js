/**
 * Simple safety checks for dev scripts.
 * Always throw - no ambiguity.
 */

const PRODUCTION_PROJECTS = [
  'muttville-prod',
  'muttville-production'
];

/**
 * Get the current project ID from environment variables.
 * @returns {string} The project ID
 */
function getProjectId() {
  return process.env.FIREBASE_PROJECT_ID || process.env.GCP_PROJECT;
}

/**
 * Check if a project ID is safe for development operations.
 * @param {string} projectId - The project ID to check
 * @returns {boolean} True if the project is safe for dev operations
 */
function isSafeProject(projectId) {
  return !PRODUCTION_PROJECTS.includes(projectId);
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
 * @param {string} projectId - The project ID to check
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
 * @param {string} projectId - The project ID to check
 * @throws {Error} If either dev scripts are not enabled or project is not safe
 */
function assertSafeForDestructiveOps(projectId) {
  assertDevScriptsEnabled();
  assertSafeProject(projectId, { allowDestructive: true });
}

/**
 * Unified safety assertion API.
 * Single entry point for all safety checks.
 * @param {Object} options - Safety options
 * @param {boolean} options.allowDestructive - Whether this is a destructive operation (default: false)
 * @throws {Error} If operation is not safe
 */
function assertSafe(options = {}) {
  const { allowDestructive = false } = options;
  const projectId = getProjectId();

  if (!projectId) {
    throw new Error('FIREBASE_PROJECT_ID or GCP_PROJECT environment variable required');
  }

  assertSafeProject(projectId, { allowDestructive });
}

module.exports = {
  isSafeProject,
  assertDevScriptsEnabled,
  assertSafeProject,
  assertSafeForDestructiveOps,
  assertSafe
};

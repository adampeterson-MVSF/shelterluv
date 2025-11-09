/**
 * Centralized Firebase safety configuration.
 * Defines allowed/unsafe project IDs for all dev scripts.
 */

const ALLOWED_PROJECT_IDS = [
  'dev-muttville',
  'staging-muttville',
  'muttville-demo'
];

const PRODUCTION_PROJECT_IDS = [
  'muttville-prod',
  'muttville-production'
];

/**
 * Check if a project ID is a production project.
 * @param {string} projectId - The Firebase project ID
 * @returns {boolean} True if project is production
 */
function isProdProjectId(projectId) {
  return PRODUCTION_PROJECT_IDS.includes(projectId);
}

/**
 * Assert that a project is not production.
 * Prevents accidental operations against production projects.
 * @param {string} projectId - The Firebase project ID to check
 * @param {string} [purpose] - Description of the operation for error messages
 * @throws {Error} If project is production
 */
function assertNotProdProject(projectId, purpose = 'operation') {
  if (!projectId) {
    throw new Error(`No project ID provided for ${purpose}`);
  }

  if (isProdProjectId(projectId)) {
    throw new Error(
      `Project "${projectId}" is a production project and cannot be used for ${purpose}.\n` +
      `Allowed projects: ${ALLOWED_PROJECT_IDS.join(', ')}`
    );
  }

  if (!ALLOWED_PROJECT_IDS.includes(projectId)) {
    throw new Error(
      `Project "${projectId}" is not in the allowlist for ${purpose}.\n` +
      `Allowed projects: ${ALLOWED_PROJECT_IDS.join(', ')}`
    );
  }
}

module.exports = {
  ALLOWED_PROJECT_IDS,
  PRODUCTION_PROJECT_IDS,
  isProdProjectId,
  assertNotProdProject
};

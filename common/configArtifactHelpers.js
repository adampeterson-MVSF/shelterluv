/**
 * Helper functions for config artifact access.
 * Pure functions that operate on the generated config artifact.
 *
 * This separates business logic from generated data.
 */

const { CONFIG_ARTIFACT } = require('./configArtifact');

/**
 * Get environment profiles configuration.
 * @returns {object} Environment profiles mapping
 */
function getEnvProfiles() {
  return CONFIG_ARTIFACT.env_profiles;
}

/**
 * Get list of safe profile names.
 * @returns {string[]} Array of safe profile names
 */
function getSafeProfiles() {
  return CONFIG_ARTIFACT.safe_profiles;
}

/**
 * Get list of valid user roles.
 * @returns {string[]} Array of role names
 */
function getRoles() {
  return CONFIG_ARTIFACT.roles;
}

/**
 * Get profile safety mapping.
 * @returns {object} Profile safety mapping
 */
function getProfileSafetyMap() {
  return CONFIG_ARTIFACT.profile_safety_map;
}

/**
 * Get project safety mapping.
 * @returns {object} Project safety mapping
 */
function getProjectSafetyMap() {
  return CONFIG_ARTIFACT.project_safety_map;
}

/**
 * Check if a profile name is safe.
 * @param {string} profileName - Profile name to check
 * @returns {boolean} True if profile is safe
 */
function isProfileSafe(profileName) {
  return CONFIG_ARTIFACT.profile_safety_map[profileName]?.is_safe || false;
}

/**
 * Check if a project ID is safe.
 * @param {string} projectId - Project ID to check
 * @returns {boolean} True if project is safe
 */
function isProjectSafe(projectId) {
  return CONFIG_ARTIFACT.project_safety_map[projectId]?.is_safe || false;
}

module.exports = {
  getEnvProfiles,
  getSafeProfiles,
  getRoles,
  getProfileSafetyMap,
  getProjectSafetyMap,
  isProfileSafe,
  isProjectSafe
};

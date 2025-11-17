/**
 * Re-export module for config data access.
 * DEPRECATED: Import directly from './configArtifact' instead.
 *
 * This module exists only for backward compatibility during migration.
 * New code should import from './configArtifact'.
 */

const {
  CONFIG_ARTIFACT,
  getEnvProfiles,
  getSafeProfiles,
  getRoles,
  getProfileSafetyMap,
  getProjectSafetyMap,
  isProfileSafe,
  isProjectSafe
} = require('./configArtifact');

module.exports = {
  // Re-export everything from configArtifact
  CONFIG_ARTIFACT,
  getEnvProfiles,
  getSafeProfiles,
  getRoles,
  getNormalizedProfileMap: getProfileSafetyMap, // alias for backward compatibility
  getProjectSafetyMap,
  isProfileSafe,
  isProjectSafe
};


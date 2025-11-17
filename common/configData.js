/**
 * Single source of truth for loading and validating common/config.json.
 * All modules that need config data should import from here.
 * 
 * This module provides:
 * - Validated config structure
 * - Type-safe accessors
 * - Consistency checks between profiles
 */

const fs = require('fs');
const path = require('path');

const configPath = path.join(__dirname, 'config.json');

let cachedConfig = null;

/**
 * Load and validate config from a JS object (pure function).
 * Performs all structure validation and normalization without file I/O.
 * @param {Object} rawConfig - Raw config object to validate and normalize
 * @returns {Object} Validated and normalized config object
 * @throws {Error} If config structure is invalid
 */
function loadConfigFromObject(rawConfig) {
  if (!rawConfig || typeof rawConfig !== 'object') {
    throw new Error('Config must be a valid object');
  }

  // Validate required structure
  if (!rawConfig.env_profiles || typeof rawConfig.env_profiles !== 'object') {
    throw new Error('config missing or invalid env_profiles object');
  }

  if (!rawConfig.python_env_profiles || typeof rawConfig.python_env_profiles !== 'object') {
    throw new Error('config missing or invalid python_env_profiles object');
  }

  if (!Array.isArray(rawConfig.safe_profiles)) {
    throw new Error('config missing or invalid safe_profiles array');
  }

  if (!Array.isArray(rawConfig.roles)) {
    throw new Error('config missing or invalid roles array');
  }

  // Validate that all python_env_profiles have valid structure first
  for (const [profileName, profileConfig] of Object.entries(rawConfig.python_env_profiles)) {
    if (!profileConfig.gcp_project || typeof profileConfig.gcp_project !== 'string') {
      throw new Error(
        `config: python_env_profiles.${profileName}.gcp_project is missing or invalid`
      );
    }
  }

  // Validate that all safe_profiles have corresponding python_env_profiles entries
  for (const profileName of rawConfig.safe_profiles) {
    if (!rawConfig.python_env_profiles[profileName]) {
      throw new Error(
        `config: safe_profiles includes "${profileName}" but python_env_profiles.${profileName} is missing`
      );
    }
    // gcp_project validation is now handled above for all profiles
  }

  // Cross-language sanity check: ensure consistency between safe_profiles and python_env_profiles
  const pythonProfileNames = Object.keys(rawConfig.python_env_profiles);
  const safeProfileNames = rawConfig.safe_profiles;

  // Check that all safe profiles exist in python_env_profiles (already done above)
  // Additional check: ensure there are production profiles (not safe)
  const productionProfiles = pythonProfileNames.filter(name => !safeProfileNames.includes(name));
  if (productionProfiles.length === 0) {
    throw new Error(
      'config: No production profiles found. At least one profile should exist in python_env_profiles but not in safe_profiles'
    );
  }

  // Document invariants in code comments
  // safe_profiles ⊆ python_env_profiles (all safe profiles have corresponding python profiles)
  // production_profiles = python_env_profiles - safe_profiles (non-empty set)
  // All python_env_profiles have gcp_project strings

  return rawConfig;
}

/**
 * Load and validate config.json structure.
 * Caches result to avoid repeated file reads.
 * @returns {Object} Validated config object
 * @throws {Error} If config structure is invalid
 */
function loadConfig() {
  if (cachedConfig) {
    return cachedConfig;
  }

  const rawConfig = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  cachedConfig = loadConfigFromObject(rawConfig);
  return cachedConfig;
}

/**
 * Get environment variable profiles.
 * @returns {Object} env_profiles object
 */
function getEnvProfiles() {
  return loadConfig().env_profiles;
}

/**
 * Get Python environment profiles (GCP project mappings).
 * @returns {Object} python_env_profiles object
 */
function getPythonEnvProfiles() {
  return loadConfig().python_env_profiles;
}

/**
 * Get list of safe (non-production) profile names.
 * @returns {string[]} Array of safe profile names
 */
function getSafeProfiles() {
  return loadConfig().safe_profiles;
}

/**
 * Get list of valid user roles.
 * @returns {string[]} Array of role names
 */
function getRoles() {
  return loadConfig().roles;
}

/**
 * Get normalized profile map for safety checks.
 * Single source of truth for profile -> {project_id, is_safe} mappings.
 * Used by both JS and Python safety logic to avoid duplication.
 * @returns {Object} Mapping of profile name -> {gcp_project: string, is_safe: boolean}
 */
function getNormalizedProfileMap() {
  const config = loadConfig();
  const result = {};

  // Include all python env profiles with computed safety
  for (const [profileName, profileConfig] of Object.entries(config.python_env_profiles)) {
    result[profileName] = {
      gcp_project: profileConfig.gcp_project,
      is_safe: config.safe_profiles.includes(profileName)
    };
  }

  return result;
}

/**
 * Get reverse normalized profile map for project-based lookups.
 * Single source of truth for project_id -> {profile_name, is_safe} mappings.
 * Used by both JS and Python when you have a project ID and need profile info.
 * @returns {Object} Mapping of project ID -> {env_profile_name: string, is_safe: boolean}
 */
function getProjectSafetyMap() {
  const config = loadConfig();
  const result = {};

  // Include all python env profiles with computed safety
  for (const [profileName, profileConfig] of Object.entries(config.python_env_profiles)) {
    result[profileConfig.gcp_project] = {
      env_profile_name: profileName,
      is_safe: config.safe_profiles.includes(profileName)
    };
  }

  return result;
}

/**
 * @deprecated Use getNormalizedProfileMap() instead.
 * Kept for backward compatibility during migration.
 */
function getCrossLanguageConfig() {
  return getNormalizedProfileMap();
}

/**
 * Clear cached config (useful for testing).
 */
function clearCache() {
  cachedConfig = null;
}

module.exports = {
  // Public API - only expose high-level accessors
  getEnvProfiles,
  getPythonEnvProfiles,
  getSafeProfiles,
  getRoles,
  getNormalizedProfileMap,
  getProjectSafetyMap,

  // For testing and config artifacts - pure loader
  loadConfigFromObject,

  // Internal - deprecated, use high-level accessors
  loadConfig, // kept for backward compatibility
  getCrossLanguageConfig, // deprecated
  clearCache
};


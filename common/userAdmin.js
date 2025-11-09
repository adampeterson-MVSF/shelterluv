/**
 * User admin utilities for CLI scripts.
 * Provides throwing versions of validation functions for cleaner script code.
 */

const { VALID_ROLES } = require('./userRoles');
const { validateEmail, validateRole, addOrUpdateUser } = require('./userManagement');

/**
 * Ensure email is valid and from allowed domains. Throws on failure.
 * @param {string} email - Email to validate
 * @param {string[]} allowedDomains - Array of allowed domains
 * @returns {string} Validated email (lowercased, trimmed)
 * @throws {Error} If email is invalid or domain not allowed
 */
function ensureAllowedDomain(email, allowedDomains = ['muttville.org']) {
  const result = validateEmail(email, allowedDomains);
  if (!result.success) {
    throw new Error(result.error);
  }
  return result.email;
}

/**
 * Ensure role is valid. Throws on failure.
 * @param {string} role - Role to validate
 * @returns {string} Validated role
 * @throws {Error} If role is invalid
 */
function ensureValidRole(role) {
  const result = validateRole(role);
  if (!result.success) {
    throw new Error(result.error);
  }
  return result.role;
}

/**
 * Upsert a user with validation. Throws on failure.
 * @param {Object} options - Options object
 * @param {Object} options.db - Firestore database instance
 * @param {Object} options.auth - Firebase Auth instance
 * @param {string} options.email - User email
 * @param {string} options.uid - Firebase Auth UID
 * @param {string} options.role - User role
 * @param {boolean} options.dryRun - Whether to perform a dry run
 * @returns {Object} Result from addOrUpdateUser
 * @throws {Error} If user operation fails
 */
async function upsertUser({ db, auth, email, uid, role, dryRun = false }) {
  const result = await addOrUpdateUser(db, auth, email, uid, role, { dryRun });
  if (!result.success) {
    throw new Error(result.error);
  }
  return result;
}

module.exports = {
  ensureAllowedDomain,
  ensureValidRole,
  upsertUser
};

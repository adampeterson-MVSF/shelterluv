/**
 * Shared user role constants and validation - CommonJS version for Node scripts.
 * Duplicated from the ES module version for compatibility.
 */

const VALID_ROLES = ['viewer', 'closer', 'staff'];

/**
 * Assert that a role is valid, throwing an error if not.
 * @param {string} role - The role to validate
 * @throws {Error} If role is invalid
 */
function assertValidRole(role) {
  if (!VALID_ROLES.includes(role)) {
    throw new Error(`Invalid role: ${role}`);
  }
}

/**
 * Validate that a role string is one of the valid roles.
 * @param {string} role - The role to validate
 * @returns {boolean} True if valid, false otherwise
 */
function isValidRole(role) {
  return VALID_ROLES.includes(role);
}

/**
 * Get all valid role values.
 * @returns {string[]} Array of valid role strings
 */
function getValidRoles() {
  return [...VALID_ROLES];
}

/**
 * Check if a role has staff privileges.
 * @param {string} role - The role to check
 * @returns {boolean} True if the role has staff privileges
 */
function isStaff(role) {
  return role === 'staff';
}

/**
 * Check if a role has admin privileges (alias for isStaff since staff is the highest level).
 * @param {string} role - The role to check
 * @returns {boolean} True if the role has admin privileges
 */
function isAdmin(role) {
  return isStaff(role);
}

module.exports = {
  VALID_ROLES,
  assertValidRole,
  isValidRole,
  getValidRoles,
  isStaff,
  isAdmin
};

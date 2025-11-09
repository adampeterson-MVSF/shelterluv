/**
 * Shared user role constants and validation.
 * Used across Node.js dev tools and React app.
 */

const VALID_ROLES = {
  VIEWER: 'viewer',
  CLOSER: 'closer',
  STAFF: 'staff'
};

const VALID_ROLE_VALUES = Object.values(VALID_ROLES);

/**
 * Assert that a role is valid, throwing an error if not.
 * @param {string} role - The role to validate
 * @throws {Error} If role is invalid
 */
function assertValidRole(role) {
  if (!VALID_ROLE_VALUES.includes(role)) {
    throw new Error(`Invalid role: ${role}`);
  }
}

/**
 * Validate that a role string is one of the valid roles.
 * @param {string} role - The role to validate
 * @returns {boolean} True if valid, false otherwise
 */
function isValidRole(role) {
  return VALID_ROLE_VALUES.includes(role);
}

/**
 * Get all valid role values for iteration.
 * @returns {string[]} Array of valid role strings
 */
function getValidRoles() {
  return [...VALID_ROLE_VALUES];
}

/**
 * Check if a role has staff privileges (staff role).
 * @param {string} role - The role to check
 * @returns {boolean} True if the role has staff privileges
 */
function isStaff(role) {
  return role === VALID_ROLES.STAFF;
}

/**
 * Check if a role has admin privileges (alias for isStaff since staff is the highest level).
 * @param {string} role - The role to check
 * @returns {boolean} True if the role has admin privileges
 */
function isAdmin(role) {
  return isStaff(role);
}

export {
  VALID_ROLES,
  VALID_ROLE_VALUES,
  assertValidRole,
  isValidRole,
  getValidRoles,
  isStaff,
  isAdmin,
};

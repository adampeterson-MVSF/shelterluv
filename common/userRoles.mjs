/**
 * ES6 module version of user role constants and validation.
 * Single source of truth for roles across webapp and scripts.
 * For webapp (bundled), roles are inlined. For Node scripts, use userRoles.js which loads from config.json.
 */

// Inlined roles - webapp bundles this, so we can't use fs at runtime
// Node scripts should use userRoles.js which loads from config.json
export const ROLES = ['viewer', 'closer', 'staff'];
export const VALID_ROLES = ROLES; // Alias for backward compatibility

/**
 * Validate that a role string is one of the valid roles.
 * @param {string} role - The role to validate
 * @returns {boolean} True if valid, false otherwise
 */
export function isValidRole(role) {
  return ROLES.includes(role);
}

/**
 * Assert that a role is valid, throwing an error if not.
 * @param {string} role - The role to validate
 * @throws {Error} If the role is not valid
 */
export function assertValidRole(role) {
  if (!isValidRole(role)) {
    throw new Error(`Invalid role "${role}"`);
  }
}

/**
 * Check if a role has staff privileges.
 * @param {string} role - The role to check
 * @returns {boolean} True if the role has staff privileges
 */
export function isStaff(role) {
  return role === 'staff';
}

/**
 * Check if a user role meets a required role level.
 * Role hierarchy: viewer < closer < staff
 * @param {string} userRole - The user's role
 * @param {string} requiredRole - The minimum required role
 * @returns {boolean} True if userRole meets or exceeds requiredRole
 */
export function hasRole(userRole, requiredRole) {
  if (!isValidRole(userRole) || !isValidRole(requiredRole)) {
    return false;
  }
  
  const hierarchy = { viewer: 0, closer: 1, staff: 2 };
  return hierarchy[userRole] >= hierarchy[requiredRole];
}

/**
 * Check if a user role matches any role in a list.
 * @param {string} userRole - The user's role
 * @param {string[]} roleList - List of allowed roles
 * @returns {boolean} True if userRole is in roleList
 */
export function hasAnyRole(userRole, roleList) {
  if (!isValidRole(userRole) || !Array.isArray(roleList)) {
    return false;
  }
  return roleList.includes(userRole);
}

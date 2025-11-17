/**
 * Shared user role constants and validation.
 * Single source of truth for roles across webapp and scripts.
 * Data-driven permission system with explicit capability mapping.
 * Loads roles from common/config.json via configData.
 */

const { getRoles } = require('./configArtifact');

const ROLES = getRoles();

/**
 * Permission capabilities mapped to roles.
 * Each role inherits capabilities from lower roles in hierarchy.
 * viewer < closer < staff
 */
const PERMISSIONS = {
  viewDogs: ['viewer', 'closer', 'staff'],
  viewFosterInfo: ['closer', 'staff'],
  editDogs: ['staff'],
  manageUsers: ['staff']
};

/**
 * Validate that a role string is one of the valid roles.
 * @param {string} role - The role to validate
 * @returns {boolean} True if valid, false otherwise
 */
function isValidRole(role) {
  return ROLES.includes(role);
}

/**
 * Assert that a role is valid, throwing an error if not.
 * @param {string} role - The role to validate
 * @throws {Error} If the role is not valid
 */
function assertValidRole(role) {
  if (!isValidRole(role)) {
    throw new Error(`Invalid role "${role}". Valid roles: ${ROLES.join(', ')}`);
  }
}

/**
 * Check if a role has a specific permission.
 * Data-driven: uses PERMISSIONS mapping instead of hardcoded checks.
 * @param {string} role - The role to check
 * @param {string} permission - The permission to check (e.g., 'viewFosterInfo')
 * @returns {boolean} True if the role has the permission
 */
function can(role, permission) {
  if (!isValidRole(role)) {
    return false;
  }
  
  const allowedRoles = PERMISSIONS[permission];
  if (!allowedRoles) {
    return false;
  }
  
  return allowedRoles.includes(role);
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
 * Check if a user role meets a required role level.
 * Role hierarchy: viewer < closer < staff
 * @param {string} userRole - The user's role
 * @param {string} requiredRole - The minimum required role
 * @returns {boolean} True if userRole meets or exceeds requiredRole
 */
function hasRole(userRole, requiredRole) {
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
function hasAnyRole(userRole, roleList) {
  if (!isValidRole(userRole) || !Array.isArray(roleList)) {
    return false;
  }
  return roleList.includes(userRole);
}

// Alias for backward compatibility
const VALID_ROLES = ROLES;

module.exports = {
  ROLES,
  VALID_ROLES,
  PERMISSIONS,
  isValidRole,
  assertValidRole,
  can,
  isStaff,
  hasRole,
  hasAnyRole
};

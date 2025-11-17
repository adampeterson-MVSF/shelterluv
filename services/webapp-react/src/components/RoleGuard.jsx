import PropTypes from 'prop-types';
import { useAuth } from '../contexts/AuthContext';
import { VALID_ROLES } from '@common/userRoles.mjs';

/**
 * Custom PropTypes validator for role arrays.
 * Ensures all roles in the array are valid.
 */
function rolesValidator(propValue, ...args) {
  const invalidRoles = propValue.filter(role => !VALID_ROLES.includes(role));
  if (invalidRoles.length > 0) {
    const [, , componentName, , propFullName] = args;
    return new Error(
      `Invalid prop \`${propFullName}\` supplied to \`${componentName}\`. ` +
      `Invalid roles: ${invalidRoles.join(', ')}. ` +
      `Valid roles are: ${VALID_ROLES.join(', ')}`
    );
  }
  return null;
}

/**
 * Guards content based on user roles.
 * Shows children only if user has one of the required roles.
 * Shows nothing (or forbidden message) if user lacks required roles.
 */
export function RoleGuard({ roles, children, fallback = null }) {
  const { authState, hasAnyRole } = useAuth();

  // Don't render anything while auth is loading
  if (authState.kind === 'loading') {
    return null;
  }

  // Show forbidden state for unauthorized users
  if (authState.kind === 'forbidden' || authState.kind === 'anonymous') {
    return fallback;
  }

  // Check if user has any of the required roles
  if (!hasAnyRole(roles)) {
    return fallback;
  }

  // User is authorized, show the content
  return <>{children}</>;
}

RoleGuard.propTypes = {
  roles: function(props, propName, componentName) {
    const propValue = props[propName];
    if (!Array.isArray(propValue)) {
      return new Error(`Invalid prop \`${propName}\` supplied to \`${componentName}\`. Expected an array.`);
    }
    return rolesValidator(propValue, null, componentName, 'prop', propName);
  },
  children: PropTypes.node.isRequired,
  fallback: PropTypes.node
};

/**
 * Convenience wrapper for staff-only content.
 * Equivalent to <RoleGuard roles={['staff']}>...</RoleGuard>
 */
export function StaffOnly({ children, fallback = null }) {
  return (
    <RoleGuard roles={['staff']} fallback={fallback}>
      {children}
    </RoleGuard>
  );
}

StaffOnly.propTypes = {
  children: PropTypes.node.isRequired,
  fallback: PropTypes.node
};

import PropTypes from 'prop-types';
import { useAuth } from '../contexts/AuthContext';

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
  roles: PropTypes.arrayOf(PropTypes.string).isRequired,
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

import PropTypes from 'prop-types';
import { useAuth } from '../contexts/AuthContext';
import { AUTH_STATE_KINDS } from '../contexts/AuthContext';
import {
  LoadingState,
  AnonymousState,
  ForbiddenState
} from './PageStates';

/**
 * Centralized auth gating component.
 * Handles all auth state checks and renders appropriate states.
 * Pages should use this instead of duplicating auth checks.
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children - Content to render when authenticated
 * @param {React.ReactNode} props.loadingFallback - Custom loading state (optional)
 * @param {React.ReactNode} props.anonymousFallback - Custom anonymous state (optional)
 * @param {React.ReactNode} props.forbiddenFallback - Custom forbidden state (optional)
 */
export function AuthGate({ 
  children, 
  loadingFallback = null, 
  anonymousFallback = null, 
  forbiddenFallback = null 
}) {
  const { authState } = useAuth();

  // Use helper functions instead of open-coding state checks
  if (authState.kind === AUTH_STATE_KINDS.LOADING) {
    return loadingFallback || <LoadingState />;
  }
  
  if (authState.kind === AUTH_STATE_KINDS.ANONYMOUS) {
    return anonymousFallback || <AnonymousState />;
  }
  
  if (authState.kind === AUTH_STATE_KINDS.FORBIDDEN) {
    return forbiddenFallback || <ForbiddenState />;
  }

  // Authenticated - render children
  return <>{children}</>;
}

AuthGate.propTypes = {
  children: PropTypes.node.isRequired,
  loadingFallback: PropTypes.node,
  anonymousFallback: PropTypes.node,
  forbiddenFallback: PropTypes.node
};


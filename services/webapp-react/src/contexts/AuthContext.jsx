/* eslint-disable react-refresh/only-export-components */
import PropTypes from 'prop-types';
import { createContext, useContext, useReducer, useEffect } from 'react';
import { authService } from '../app';
import { hasRole as hasRoleHierarchy, hasAnyRole as hasAnyRoleCheck } from '@common/userRoles.mjs';

// Auth state union types - fixed set of possible states
export const AUTH_STATE_KINDS = {
  LOADING: 'loading',
  ANONYMOUS: 'anonymous',
  FORBIDDEN: 'forbidden',
  AUTHENTICATED: 'authenticated'
};

// Auth state reducer - pure function for state transitions
function authReducer(state, action) {
  switch (action.type) {
    case 'AUTH_LOADING':
      return { kind: AUTH_STATE_KINDS.LOADING };
    case 'AUTH_ANONYMOUS':
      return { kind: AUTH_STATE_KINDS.ANONYMOUS };
    case 'AUTH_FORBIDDEN':
      return { kind: AUTH_STATE_KINDS.FORBIDDEN, user: action.user };
    case 'AUTH_AUTHENTICATED':
      return { kind: AUTH_STATE_KINDS.AUTHENTICATED, user: action.user, role: action.role };
    default:
      return state;
  }
}

const AuthContext = createContext(null);

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Pure function to handle Firebase user → auth state transition
function handleFirebaseUser(firebaseUser, authServiceDep, dispatch) {
  if (firebaseUser) {
    authServiceDep.getUserRole(firebaseUser.uid).then(result => {
      if (result.success) {
        if (result.data === null) {
          console.warn(`Forbidden access attempt from ${firebaseUser.email} (UID: ${firebaseUser.uid}) - no user document`);
          dispatch({ type: 'AUTH_FORBIDDEN', user: firebaseUser });
        } else {
          dispatch({ type: 'AUTH_AUTHENTICATED', user: firebaseUser, role: result.data });
        }
      } else {
        console.error('Error fetching user role:', result.error);
        dispatch({ type: 'AUTH_FORBIDDEN', user: firebaseUser });
      }
    });
  } else {
    dispatch({ type: 'AUTH_ANONYMOUS' });
  }
}

function useAuthStateManagement(authServiceDep, dispatch) {
  useEffect(() => {
    const unsubscribe = authServiceDep.subscribeToAuthChanges((firebaseUser) => {
      handleFirebaseUser(firebaseUser, authServiceDep, dispatch);
    });
    return () => unsubscribe();
  }, [authServiceDep, dispatch]);
}

function createAuthActions(authServiceDep) {
  const login = async () => {
    try {
      await authServiceDep.signInWithGoogle();
      return { success: true };
    } catch (error) {
      console.error('Login failed:', error);
      return { success: false, error: error.message };
    }
  };

  const logout = async () => {
    try {
      await authServiceDep.signOutUser();
      return { success: true };
    } catch (error) {
      console.error('Logout failed:', error);
      return { success: false, error: error.message };
    }
  };

  return { login, logout };
}

function createAuthHelpers(authState) {
  // Use shared role hierarchy functions from common/userRoles.mjs
  const hasRole = (requiredRole) => {
    return authState.kind === 'authenticated' && hasRoleHierarchy(authState.role, requiredRole);
  };

  const hasAnyRole = (roles) => {
    return authState.kind === 'authenticated' && hasAnyRoleCheck(authState.role, roles);
  };

  const isAuthenticated = authState.kind === 'authenticated';
  const isForbidden = authState.kind === 'forbidden';
  const canViewDogs = authState.kind === 'authenticated';

  return { hasRole, hasAnyRole, isAuthenticated, isForbidden, canViewDogs };
}

/**
 * Standalone helper functions for auth state checks.
 * Use these instead of open-coding state machine logic.
 */
export function isAuthenticated(authState) {
  return authState.kind === AUTH_STATE_KINDS.AUTHENTICATED;
}

export function isForbidden(authState) {
  return authState.kind === AUTH_STATE_KINDS.FORBIDDEN;
}

export function canViewDogs(authState) {
  return authState.kind === AUTH_STATE_KINDS.AUTHENTICATED;
}

export function shouldHideDogs(authState) {
  return authState.kind === AUTH_STATE_KINDS.ANONYMOUS || authState.kind === AUTH_STATE_KINDS.FORBIDDEN;
}

export function AuthProvider({
  children,
  authService: authServiceDep = authService
}) {
  const [authState, dispatch] = useReducer(authReducer, { kind: 'loading' });

  useAuthStateManagement(authServiceDep, dispatch);

  const { login, logout } = createAuthActions(authServiceDep);
  const { hasRole, hasAnyRole, isAuthenticated } = createAuthHelpers(authState);

  const value = {
    authState,
    login,
    logout,
    hasRole,
    hasAnyRole,
    isAuthenticated
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

AuthProvider.propTypes = {
  children: PropTypes.node.isRequired,
  authService: PropTypes.object
};

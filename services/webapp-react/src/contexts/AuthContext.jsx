/* eslint-disable react-refresh/only-export-components */
import PropTypes from 'prop-types';
import { createContext, useContext, useReducer, useEffect } from 'react';
import { authService } from '../app';
import { getUserRole } from '../repositories/userRepository';

// Auth state reducer - pure function for state transitions
function authReducer(state, action) {
  switch (action.type) {
    case 'AUTH_LOADING':
      return { kind: 'loading' };
    case 'AUTH_ANONYMOUS':
      return { kind: 'anonymous' };
    case 'AUTH_FORBIDDEN':
      return { kind: 'forbidden', user: action.user };
    case 'AUTH_AUTHENTICATED':
      return { kind: 'authenticated', user: action.user, role: action.role };
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
function handleFirebaseUser(firebaseUser, getUserRoleDep, dispatch) {
  if (firebaseUser) {
    getUserRoleDep(firebaseUser.uid).then(result => {
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

function useAuthStateManagement(authServiceDep, getUserRoleDep, dispatch) {
  useEffect(() => {
    const unsubscribe = authServiceDep.subscribeToAuthChanges((firebaseUser) => {
      handleFirebaseUser(firebaseUser, getUserRoleDep, dispatch);
    });
    return () => unsubscribe();
  }, [authServiceDep, getUserRoleDep, dispatch]);
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
  const hasRole = (requiredRole) => {
    return authState.kind === 'authenticated' && authState.role === requiredRole;
  };

  const hasAnyRole = (roles) => {
    return authState.kind === 'authenticated' && roles.includes(authState.role);
  };

  const isAuthenticated = authState.kind === 'authenticated';

  return { hasRole, hasAnyRole, isAuthenticated };
}

export function AuthProvider({
  children,
  authService: authServiceDep = authService,
  getUserRole: getUserRoleDep = getUserRole
}) {
  const [authState, dispatch] = useReducer(authReducer, { kind: 'loading' });

  useAuthStateManagement(authServiceDep, getUserRoleDep, dispatch);

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
  authService: PropTypes.object,
  getUserRole: PropTypes.func
};

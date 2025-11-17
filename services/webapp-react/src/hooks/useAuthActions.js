import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

/**
 * Custom hook for auth actions with error handling
 * Provides login/logout functions with consistent error state management
 */
export function useAuthActions() {
  const { login, logout } = useAuth();
  const [error, setError] = useState(null);

  const handleLogin = async () => {
    setError(null);
    const result = await login();
    if (!result.success) {
      console.error('Login failed:', result.error);
      setError('Login failed. Please try again.');
      return false;
    }
    return true;
  };

  const handleLogout = async () => {
    setError(null);
    const result = await logout();
    if (!result.success) {
      console.error('Logout failed:', result.error);
      setError('Logout failed. Please try again.');
      return false;
    }
    return true;
  };

  return {
    error,
    setError,
    handleLogin,
    handleLogout
  };
}

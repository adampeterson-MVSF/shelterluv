import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';

// No global mocking - tests use dependency injection via AuthProvider props

// Test component that uses the auth context
function TestComponent({ onLogin, onLogout, onReady }) {
  const { authState, login, logout } = useAuth();

  React.useEffect(() => {
    if (onLogin) onLogin(login);
    if (onLogout) onLogout(logout);
    if (onReady) onReady({ login, logout });
  }, [onLogin, onLogout, onReady, login, logout]);

  return (
    <div>
      <div data-testid="status">{authState.kind}</div>
      <div data-testid="user">{authState.user ? 'user-present' : 'no-user'}</div>
      <div data-testid="role">{authState.role || 'no-role'}</div>
    </div>
  );
}

// Helper to create a mock Firebase user
const createMockFirebaseUser = (overrides = {}) => ({
  uid: 'test-uid',
  email: 'user@muttville.org',
  displayName: 'Test User',
  ...overrides
});

// Helper to render with auth context using DI
function renderWithAuth(overrides = {}) {
  let authChangeCallback;
  const unsubscribeMock = vi.fn();

  const mockGetRole = overrides.getUserRole || vi.fn().mockResolvedValue({ success: true, data: null });

  const fakeAuthService = {
    subscribeToAuthChanges: vi.fn((cb) => {
      authChangeCallback = cb;
      return unsubscribeMock;
    }),
    signInWithGoogle: vi.fn(),
    signOutUser: vi.fn(),
    getUserRole: mockGetRole,
  };

  const result = render(
    <AuthProvider authService={fakeAuthService}>
      <TestComponent />
    </AuthProvider>
  );

  return {
    ...result,
    simulateAuthChange: (user) => {
      if (!authChangeCallback) {
        throw new Error('authChangeCallback not initialized');
      }
      authChangeCallback(user);
    }
  };
}

describe('AuthContext', () => {

  describe('useAuth hook', () => {
    it('throws when used outside AuthProvider', () => {
      // Create a component that uses useAuth without a provider
      function ComponentWithoutProvider() {
        const auth = useAuth(); // This should throw
        return <div>{auth.authState.kind}</div>;
      }

      // Expect the component to throw when rendered without provider
      // The error happens during React's render phase, so we need to catch it
      let error;
      try {
        render(<ComponentWithoutProvider />);
      } catch (e) {
        error = e;
      }

      expect(error).toBeDefined();
      expect(error.message).toBe('useAuth must be used within an AuthProvider');
    });
  });

  describe('Initial state', () => {
    it('starts with loading status then transitions to anonymous after auth initialization', async () => {
      const { simulateAuthChange } = renderWithAuth();

      // Initially should be loading
      expect(screen.getByTestId('status')).toHaveTextContent('loading');

      // Tell the subscription "there is no user"
      await simulateAuthChange(null);

      await waitFor(() => {
        expect(screen.getByTestId('status')).toHaveTextContent('anonymous');
        expect(screen.getByTestId('user')).toHaveTextContent('no-user');
        expect(screen.getByTestId('role')).toHaveTextContent('no-role');
      });
    });
  });

  describe('Authentication state machine', () => {
    it('transitions to authenticated when user signs in with valid role', async () => {
      const mockFirebaseUser = createMockFirebaseUser();
      const mockRole = 'closer';
      const mockGetRole = vi.fn().mockResolvedValue({ success: true, data: mockRole });

      const { simulateAuthChange } = renderWithAuth({ getUserRole: mockGetRole });

      // Simulate auth state change
      await simulateAuthChange(mockFirebaseUser);

      await waitFor(() => {
        expect(screen.getByTestId('status')).toHaveTextContent('authenticated');
        expect(screen.getByTestId('user')).toHaveTextContent('user-present');
        expect(screen.getByTestId('role')).toHaveTextContent(mockRole);
      });

      expect(mockGetRole).toHaveBeenCalledWith(mockFirebaseUser.uid);
    });

    it('transitions to forbidden when user exists but has no role in database', async () => {
      const mockFirebaseUser = createMockFirebaseUser();
      const mockGetRole = vi.fn().mockResolvedValue({ success: true, data: null });

      const { simulateAuthChange } = renderWithAuth({ getUserRole: mockGetRole });

      // Simulate auth state change
      await simulateAuthChange(mockFirebaseUser);

      await waitFor(() => {
        expect(screen.getByTestId('status')).toHaveTextContent('forbidden');
        expect(screen.getByTestId('user')).toHaveTextContent('user-present');
        expect(screen.getByTestId('role')).toHaveTextContent('no-role');
      });
    });

    it('transitions to unauthenticated when user signs out', async () => {
      // First simulate authenticated user
      const mockFirebaseUser = createMockFirebaseUser();
      const mockGetRole = vi.fn().mockResolvedValue({ success: true, data: 'staff' });

      const { simulateAuthChange } = renderWithAuth({ getUserRole: mockGetRole });

      // Simulate initial auth state
      await simulateAuthChange(mockFirebaseUser);

      await waitFor(() => {
        expect(screen.getByTestId('status')).toHaveTextContent('authenticated');
      });

      // Now simulate sign out by calling the callback with null
      await simulateAuthChange(null);

      await waitFor(() => {
        expect(screen.getByTestId('status')).toHaveTextContent('anonymous');
        expect(screen.getByTestId('user')).toHaveTextContent('no-user');
        expect(screen.getByTestId('role')).toHaveTextContent('no-role');
      });
    });
  });

  describe('Login functionality', () => {
    it('calls signInWithGoogle and handles success', async () => {
      const mockSignIn = vi.fn().mockResolvedValue();
      const fakeAuthService = {
        subscribeToAuthChanges: vi.fn(() => vi.fn()),
        signInWithGoogle: mockSignIn,
        signOutUser: vi.fn(),
      };

      let capturedLogin;
      function TestConsumer() {
        const { login } = useAuth();
        React.useEffect(() => {
          capturedLogin = login;
        }, [login]);
        return <div>Test</div>;
      }

      render(
        <AuthProvider authService={fakeAuthService}>
          <TestConsumer />
        </AuthProvider>
      );

      // Call the login function
      await capturedLogin();

      expect(mockSignIn).toHaveBeenCalledTimes(1);
    });

    it('handles login errors', async () => {
      const mockError = new Error('Login failed');
      const mockSignIn = vi.fn().mockRejectedValue(mockError);
      const fakeAuthService = {
        subscribeToAuthChanges: vi.fn(() => vi.fn()),
        signInWithGoogle: mockSignIn,
        signOutUser: vi.fn(),
      };

      let capturedLogin;
      function TestConsumer() {
        const { login } = useAuth();
        React.useEffect(() => {
          capturedLogin = login;
        }, [login]);
        return <div>Test</div>;
      }

      render(
        <AuthProvider authService={fakeAuthService}>
          <TestConsumer />
        </AuthProvider>
      );

      // Call the login function and expect it to handle the error
      const result = await capturedLogin();

      expect(mockSignIn).toHaveBeenCalledTimes(1);
      expect(result.success).toBe(false);
      expect(result.error).toBe('Login failed');
    });
  });

  describe('Logout functionality', () => {
    it('calls signOutUser and handles success', async () => {
      const mockSignOut = vi.fn().mockResolvedValue();
      const fakeAuthService = {
        subscribeToAuthChanges: vi.fn(() => vi.fn()),
        signInWithGoogle: vi.fn(),
        signOutUser: mockSignOut,
      };

      let capturedLogout;
      function TestConsumer() {
        const { logout } = useAuth();
        React.useEffect(() => {
          capturedLogout = logout;
        }, [logout]);
        return <div>Test</div>;
      }

      render(
        <AuthProvider authService={fakeAuthService}>
          <TestConsumer />
        </AuthProvider>
      );

      // Call the logout function
      await capturedLogout();

      expect(mockSignOut).toHaveBeenCalledTimes(1);
    });

    it('handles logout errors', async () => {
      const mockError = new Error('Logout failed');
      const mockSignOut = vi.fn().mockRejectedValue(mockError);
      const fakeAuthService = {
        subscribeToAuthChanges: vi.fn(() => vi.fn()),
        signInWithGoogle: vi.fn(),
        signOutUser: mockSignOut,
      };

      let capturedLogout;
      function TestConsumer() {
        const { logout } = useAuth();
        React.useEffect(() => {
          capturedLogout = logout;
        }, [logout]);
        return <div>Test</div>;
      }

      render(
        <AuthProvider authService={fakeAuthService}>
          <TestConsumer />
        </AuthProvider>
      );

      // Call the logout function and expect it to handle the error
      const result = await capturedLogout();

      expect(mockSignOut).toHaveBeenCalledTimes(1);
      expect(result.success).toBe(false);
      expect(result.error).toBe('Logout failed');
    });
  });

  describe('Error handling', () => {
    it('handles getUserRole errors gracefully', async () => {
      const mockFirebaseUser = createMockFirebaseUser();
      const mockError = 'Database error';
      const mockGetRole = vi.fn().mockResolvedValue({ success: false, data: null, error: mockError });

      // Mock console.error to capture error logs
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const { simulateAuthChange } = renderWithAuth({ getUserRole: mockGetRole });

      // Simulate auth state change
      await simulateAuthChange(mockFirebaseUser);

      // Wait for the async operation to complete
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith("Error fetching user role:", mockError);
        expect(screen.getByTestId('status')).toHaveTextContent('forbidden');
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Subscription cleanup', () => {
    it('unsubscribes from auth changes on unmount', async () => {
      const unsubscribeMock = vi.fn();
      const fakeAuthService = {
        subscribeToAuthChanges: vi.fn(() => unsubscribeMock),
        signInWithGoogle: vi.fn(),
        signOutUser: vi.fn(),
      };

      const { unmount } = render(
        <AuthProvider authService={fakeAuthService}>
          <TestComponent />
        </AuthProvider>
      );

      // Wait for subscription to be called
      await waitFor(() => expect(fakeAuthService.subscribeToAuthChanges).toHaveBeenCalled());

      unmount();

      expect(unsubscribeMock).toHaveBeenCalledTimes(1);
    });
  });
});

/**
 * Tests for Header component
 */

import { describe, it, expect, vi } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { Header } from './Header.jsx';
import { renderWithProviders } from '../test/testUtils';

// Mock Firebase app initialization to prevent env var requirements
vi.mock('../app', () => ({
  db: 'mock-db-instance',
  authService: {
    signInWithGoogle: vi.fn(),
    signOutUser: vi.fn(),
    subscribeToAuthChanges: vi.fn(() => vi.fn()) // Return mock unsubscribe function
  }
}));

// Mock auth state for tests that need specific states
const mockState = {
  authState: { kind: 'loading' },
  login: vi.fn().mockResolvedValue({ success: true }),
  logout: vi.fn().mockResolvedValue({ success: true }),
  hasRole: vi.fn(),
  isAuthenticated: false
};

vi.mock('../contexts/AuthContext', async () => {
  const actual = await vi.importActual('../contexts/AuthContext');
  return {
    ...actual,
    useAuth: () => ({
      authState: mockState.authState,
      login: mockState.login,
      logout: mockState.logout,
      hasRole: mockState.hasRole,
      isAuthenticated: mockState.isAuthenticated
    })
  };
});

describe('Header', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset mock auth state
    mockState.authState = { kind: 'loading' };
    mockState.login.mockResolvedValue({ success: true });
    mockState.logout.mockResolvedValue({ success: true });
    mockState.hasRole.mockReset();
    mockState.isAuthenticated = false;
  });

  it('should render app title and sign in button when not authenticated', () => {
    mockState.authState = { kind: 'anonymous' };

    renderWithProviders(<Header />);

    expect(screen.getByText('Muttville')).toBeInTheDocument();
    expect(screen.getByText('Sign In')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('should call login when sign in button is clicked', async () => {
    mockState.authState = { kind: 'anonymous' };

    renderWithProviders(<Header />);

    const signInButton = screen.getByText('Sign In');
    fireEvent.click(signInButton);

    await waitFor(() => {
      expect(mockState.login).toHaveBeenCalledTimes(1);
    });
  });

  it('should show unauthorized message for unauthorized users', () => {
    mockState.authState = { kind: 'forbidden', user: { email: 'test@example.com' } };

    renderWithProviders(<Header />);

    expect(screen.getByText('Muttville')).toBeInTheDocument();
    expect(screen.getByText('Access denied. Only @muttville.org accounts are permitted.')).toBeInTheDocument();
    expect(screen.getByText('Sign Out')).toBeInTheDocument();

    // Should not show normal navigation
    expect(screen.queryByText('Sign In')).not.toBeInTheDocument();
  });

  it('should call logout when sign out button is clicked for unauthorized users', async () => {
    mockState.authState = { kind: 'forbidden', user: { email: 'test@example.com' } };

    renderWithProviders(<Header />);

    const signOutButton = screen.getByText('Sign Out');
    fireEvent.click(signOutButton);

    await waitFor(() => {
      expect(mockState.logout).toHaveBeenCalledTimes(1);
    });
  });

  it('should show user email and logout button when authenticated', () => {
    mockState.authState = { kind: 'authenticated', user: { email: 'user@muttville.org' }, role: 'staff' };

    renderWithProviders(<Header />);

    expect(screen.getByText('Muttville')).toBeInTheDocument();
    expect(screen.getByText('user@muttville.org')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();

    // Should not show sign in button
    expect(screen.queryByText('Sign In')).not.toBeInTheDocument();
  });

  it('should call logout when logout button is clicked for authenticated users', async () => {
    mockState.authState = { kind: 'authenticated', user: { email: 'user@muttville.org' }, role: 'staff' };

    renderWithProviders(<Header />);

    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);

    await waitFor(() => {
      expect(mockState.logout).toHaveBeenCalledTimes(1);
    });
  });

  it('should have correct CSS classes', () => {
    mockState.authState = { kind: 'authenticated', user: { email: 'user@muttville.org' }, role: 'staff' };

    const { container } = renderWithProviders(<Header />);

    expect(container.firstChild).toHaveClass('app-header');
    expect(container.querySelector('.header-content')).toBeInTheDocument();
    expect(container.querySelector('.app-title')).toBeInTheDocument();
  });

  it('should link to home page from title', () => {
    renderWithProviders(<Header />);

    const titleLink = screen.getByRole('link');
    expect(titleLink).toHaveAttribute('href', '/');
  });

  it('should handle login error gracefully', async () => {
    mockState.authState = { kind: 'anonymous' };
    mockState.login.mockResolvedValue({ success: false, error: 'Login failed' });

    renderWithProviders(<Header />);

    const signInButton = screen.getByText('Sign In');
    fireEvent.click(signInButton);

    await waitFor(() => {
      expect(screen.getByText('Login failed. Please try again.')).toBeInTheDocument();
    });

    expect(mockState.login).toHaveBeenCalledTimes(1);
  });

  it('should handle logout error gracefully', async () => {
    mockState.authState = { kind: 'authenticated', user: { email: 'user@muttville.org' }, role: 'staff' };
    mockState.logout.mockResolvedValue({ success: false, error: 'Logout failed' });

    renderWithProviders(<Header />);

    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);

    await waitFor(() => {
      expect(screen.getByText('Logout failed. Please try again.')).toBeInTheDocument();
    });

    expect(mockState.logout).toHaveBeenCalledTimes(1);
  });

});

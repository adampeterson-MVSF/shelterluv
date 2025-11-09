/**
 * Tests for Header component
 */

import { describe, it, expect, vi } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { Header } from './Header.jsx';
import { renderWithProviders } from '../test/testUtils';

// Mock auth state for tests that need specific states
let mockAuthState = { kind: 'loading' };
let mockLogin = vi.fn().mockResolvedValue({ success: true });
let mockLogout = vi.fn().mockResolvedValue({ success: true });
let mockHasRole = vi.fn();
let mockIsAuthenticated = false;

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    authState: mockAuthState,
    login: mockLogin,
    logout: mockLogout,
    hasRole: mockHasRole,
    isAuthenticated: mockIsAuthenticated
  })
}));

describe('Header', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset mock auth state
    mockAuthState = { kind: 'loading' };
    mockLogin = vi.fn().mockResolvedValue({ success: true });
    mockLogout = vi.fn().mockResolvedValue({ success: true });
    mockHasRole = vi.fn();
    mockIsAuthenticated = false;
  });

  it('should render app title and sign in button when not authenticated', () => {
    mockAuthState = { kind: 'anonymous' };

    renderWithProviders(<Header />);

    expect(screen.getByText('Muttville')).toBeInTheDocument();
    expect(screen.getByText('Sign In')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('should call login when sign in button is clicked', async () => {
    mockAuthState = { kind: 'anonymous' };

    renderWithProviders(<Header />);

    const signInButton = screen.getByText('Sign In');
    fireEvent.click(signInButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledTimes(1);
    });
  });

  it('should show unauthorized message for unauthorized users', () => {
    mockAuthState = { kind: 'forbidden', user: { email: 'test@example.com' } };

    renderWithProviders(<Header />);

    expect(screen.getByText('Muttville')).toBeInTheDocument();
    expect(screen.getByText('Access denied. Only @muttville.org accounts are permitted.')).toBeInTheDocument();
    expect(screen.getByText('Sign Out')).toBeInTheDocument();

    // Should not show normal navigation
    expect(screen.queryByText('Sign In')).not.toBeInTheDocument();
  });

  it('should call logout when sign out button is clicked for unauthorized users', async () => {
    mockAuthState = { kind: 'forbidden', user: { email: 'test@example.com' } };

    renderWithProviders(<Header />);

    const signOutButton = screen.getByText('Sign Out');
    fireEvent.click(signOutButton);

    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalledTimes(1);
    });
  });

  it('should show user email and logout button when authenticated', () => {
    mockAuthState = { kind: 'authenticated', user: { email: 'user@muttville.org' }, role: 'staff' };

    renderWithProviders(<Header />);

    expect(screen.getByText('Muttville')).toBeInTheDocument();
    expect(screen.getByText('user@muttville.org')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();

    // Should not show sign in button
    expect(screen.queryByText('Sign In')).not.toBeInTheDocument();
  });

  it('should call logout when logout button is clicked for authenticated users', async () => {
    mockAuthState = { kind: 'authenticated', user: { email: 'user@muttville.org' }, role: 'staff' };

    renderWithProviders(<Header />);

    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);

    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalledTimes(1);
    });
  });

  it('should have correct CSS classes', () => {
    mockAuthState = { kind: 'authenticated', user: { email: 'user@muttville.org' }, role: 'staff' };

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
    mockAuthState = { kind: 'anonymous' };
    mockLogin.mockResolvedValue({ success: false, error: 'Login failed' });

    renderWithProviders(<Header />);

    const signInButton = screen.getByText('Sign In');
    fireEvent.click(signInButton);

    await waitFor(() => {
      expect(screen.getByText('Login failed. Please try again.')).toBeInTheDocument();
    });

    expect(mockLogin).toHaveBeenCalledTimes(1);
  });

  it('should handle logout error gracefully', async () => {
    mockAuthState = { kind: 'authenticated', user: { email: 'user@muttville.org' }, role: 'staff' };
    mockLogout.mockResolvedValue({ success: false, error: 'Logout failed' });

    renderWithProviders(<Header />);

    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);

    await waitFor(() => {
      expect(screen.getByText('Logout failed. Please try again.')).toBeInTheDocument();
    });

    expect(mockLogout).toHaveBeenCalledTimes(1);
  });

});

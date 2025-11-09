/**
 * Tests for RoleGuard component
 */

import { describe, it, expect, vi } from 'vitest';
import { screen, render } from '@testing-library/react';
import { RoleGuard, StaffOnly } from './RoleGuard.jsx';

// Mock auth state for tests
let mockAuthState = { kind: 'loading' };
let mockHasAnyRole = vi.fn();

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    authState: mockAuthState,
    hasAnyRole: mockHasAnyRole
  })
}));

describe('RoleGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockAuthState = { kind: 'loading' };
    mockHasAnyRole = vi.fn();
  });

  it('should render nothing while auth is loading', () => {
    mockAuthState = { kind: 'loading' };

    const { container } = render(
      <RoleGuard roles={['staff']}>
        <div>Protected Content</div>
      </RoleGuard>
    );

    expect(container.firstChild).toBeNull();
  });

  it('should render fallback for anonymous users', () => {
    mockAuthState = { kind: 'anonymous' };

    render(
      <RoleGuard roles={['staff']} fallback={<div>Please sign in</div>}>
        <div>Protected Content</div>
      </RoleGuard>
    );

    expect(screen.getByText('Please sign in')).toBeInTheDocument();
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('should render fallback for forbidden users', () => {
    mockAuthState = { kind: 'forbidden' };

    render(
      <RoleGuard roles={['staff']} fallback={<div>Access denied</div>}>
        <div>Protected Content</div>
      </RoleGuard>
    );

    expect(screen.getByText('Access denied')).toBeInTheDocument();
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('should render children when user has required role', () => {
    mockAuthState = { kind: 'authenticated', user: { email: 'test@muttville.org' } };
    mockHasAnyRole.mockReturnValue(true);

    render(
      <RoleGuard roles={['staff']}>
        <div>Protected Content</div>
      </RoleGuard>
    );

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('should render fallback when user lacks required role', () => {
    mockAuthState = { kind: 'authenticated', user: { email: 'test@muttville.org' } };
    mockHasAnyRole.mockReturnValue(false);

    render(
      <RoleGuard roles={['staff']} fallback={<div>Insufficient permissions</div>}>
        <div>Protected Content</div>
      </RoleGuard>
    );

    expect(screen.getByText('Insufficient permissions')).toBeInTheDocument();
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('should render nothing when user lacks required role and no fallback provided', () => {
    mockAuthState = { kind: 'authenticated', user: { email: 'test@muttville.org' } };
    mockHasAnyRole.mockReturnValue(false);

    const { container } = render(
      <RoleGuard roles={['staff']}>
        <div>Protected Content</div>
      </RoleGuard>
    );

    expect(container.firstChild).toBeNull();
  });

  it('should support multiple roles', () => {
    mockAuthState = { kind: 'authenticated', user: { email: 'test@muttville.org' } };
    mockHasAnyRole.mockReturnValue(true);

    render(
      <RoleGuard roles={['staff', 'closer']}>
        <div>Protected Content</div>
      </RoleGuard>
    );

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
    expect(mockHasAnyRole).toHaveBeenCalledWith(['staff', 'closer']);
  });
});

describe('StaffOnly', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockAuthState = { kind: 'authenticated', user: { email: 'test@muttville.org' } };
    mockHasAnyRole = vi.fn();
  });

  it('should render children for staff users', () => {
    mockHasAnyRole.mockReturnValue(true);

    render(
      <StaffOnly>
        <div>Staff Only Content</div>
      </StaffOnly>
    );

    expect(screen.getByText('Staff Only Content')).toBeInTheDocument();
  });

  it('should render fallback for non-staff users', () => {
    mockHasAnyRole.mockReturnValue(false);

    render(
      <StaffOnly fallback={<div>Not authorized</div>}>
        <div>Staff Only Content</div>
      </StaffOnly>
    );

    expect(screen.getByText('Not authorized')).toBeInTheDocument();
    expect(screen.queryByText('Staff Only Content')).not.toBeInTheDocument();
  });

  it('should handle viewer role correctly', () => {
    mockAuthState = { kind: 'authenticated', user: { email: 'viewer@muttville.org' } };
    mockHasAnyRole.mockReturnValue(false);

    render(
      <StaffOnly fallback={<div>Access denied</div>}>
        <div>Staff Content</div>
      </StaffOnly>
    );

    expect(screen.getByText('Access denied')).toBeInTheDocument();
  });

  it('should handle closer role correctly (closer is not staff)', () => {
    mockAuthState = { kind: 'authenticated', user: { email: 'closer@muttville.org' } };
    mockHasAnyRole.mockReturnValue(false);

    render(
      <StaffOnly fallback={<div>Access denied</div>}>
        <div>Staff Content</div>
      </StaffOnly>
    );

    expect(screen.getByText('Access denied')).toBeInTheDocument();
  });

  it('should handle staff role correctly', () => {
    mockAuthState = { kind: 'authenticated', user: { email: 'staff@muttville.org' } };
    mockHasAnyRole.mockReturnValue(true);

    render(
      <StaffOnly>
        <div>Staff Content</div>
      </StaffOnly>
    );

    expect(screen.getByText('Staff Content')).toBeInTheDocument();
  });
});

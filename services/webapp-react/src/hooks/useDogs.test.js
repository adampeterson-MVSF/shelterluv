import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useDogs } from './useDogs';
import { getDogs } from '../repositories/dogRepository';

// Mock normalized Dog objects
const mockNormalizedDogs = [
  {
    id: 'dog1',
    Name: 'Buddy',
    Breed: 'Golden Retriever',
    AgeDisplay: '3 years',
    Size: 'Large',
    Gender: 'Male',
    Status: 'AVAILABLE'
  },
  {
    id: 'dog2',
    Name: 'Max',
    Breed: 'Labrador',
    AgeDisplay: '5 years',
    Size: 'Medium',
    Gender: 'Male',
    Status: 'AVAILABLE'
  }
];

// Mock the dogRepository
vi.mock('../repositories/dogRepository', () => ({
  getDogs: vi.fn()
}));

describe('useDogs', () => {
  let mockGetDogs;

  beforeEach(() => {
    mockGetDogs = vi.fn();
    getDogs.mockImplementation(mockGetDogs);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('successful fetch', () => {
    it('fetches dogs successfully when authenticated', async () => {
      mockGetDogs.mockResolvedValue({ success: true, data: mockNormalizedDogs });
      const mockAuthPermissions = { canViewDogs: true, shouldHideDogs: false };

      const { result } = renderHook(() => useDogs(mockAuthPermissions));

      // Wait for fetch to complete
      await waitFor(() => {
        expect(result.current).toEqual({
          allDogs: mockNormalizedDogs,
          loading: false,
          error: null,
          refetch: expect.any(Function),
        });
      });

      expect(mockGetDogs).toHaveBeenCalledTimes(1);
    });

    it('handles empty dogs array when authenticated', async () => {
      mockGetDogs.mockResolvedValue({ success: true, data: [] });
      const mockAuthPermissions = { canViewDogs: true, shouldHideDogs: false };

      const { result } = renderHook(() => useDogs(mockAuthPermissions));

      await waitFor(() => {
        expect(result.current).toEqual({
          allDogs: [],
          loading: false,
          error: null,
          refetch: expect.any(Function),
        });
      });
    });
  });

  describe('error handling', () => {
    it('sets error state on fetch failure when authenticated', async () => {
      const mockError = 'Firestore connection failed';
      mockGetDogs.mockResolvedValue({ success: false, data: [], error: mockError });
      const mockAuthPermissions = { canViewDogs: true, shouldHideDogs: false };

      const { result } = renderHook(() => useDogs(mockAuthPermissions));

      await waitFor(() => {
        expect(result.current).toEqual({
          allDogs: [],
          loading: false,
          error: mockError,
          refetch: expect.any(Function),
        });
      });

      expect(mockGetDogs).toHaveBeenCalledTimes(1);
    });
  });

  describe('unauthenticated state', () => {
    it('returns empty state when should hide dogs', () => {
      const mockAuthPermissions = { canViewDogs: false, shouldHideDogs: true };

      const { result } = renderHook(() => useDogs(mockAuthPermissions));

      expect(result.current).toEqual({
        allDogs: [],
        loading: false,
        error: null,
        refetch: expect.any(Function),
      });
      expect(mockGetDogs).not.toHaveBeenCalled();
    });

    it('returns empty state when forbidden', () => {
      const mockAuthPermissions = { canViewDogs: false, shouldHideDogs: true };

      const { result } = renderHook(() => useDogs(mockAuthPermissions));

      expect(result.current).toEqual({
        allDogs: [],
        loading: false,
        error: null,
        refetch: expect.any(Function),
      });
      expect(mockGetDogs).not.toHaveBeenCalled();
    });
  });
});

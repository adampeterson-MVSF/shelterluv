import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { getUserRole } from './userRepository';

/**
 * Tests for userRepository - Firebase user role management
 */

// Mock app initialization
vi.mock('../app', () => ({
  db: 'mock-db-instance'
}));

// Mock userRoles validation
vi.mock('@common/userRoles.mjs', () => ({
  ROLES: ['viewer', 'closer', 'staff']
}));

// Mock Firebase Firestore
vi.mock('firebase/firestore', () => ({
  doc: vi.fn(),
  getDoc: vi.fn()
}));

import { doc, getDoc } from 'firebase/firestore';

describe('userRepository', () => {
  let mockDoc;
  let mockGetDoc;

  beforeEach(() => {
    mockDoc = vi.fn(() => 'mock-doc-ref');
    mockGetDoc = vi.fn(() => Promise.resolve({
      exists: () => true,
      data: () => ({ role: 'staff' })
    }));

    // Override the global mocks for this test
    doc.mockImplementation(mockDoc);
    getDoc.mockImplementation(mockGetDoc);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('getUserRole', () => {

    it('returns success with null data when uid is falsy', async () => {
      expect(await getUserRole(null)).toEqual({ success: true, data: null });
      expect(await getUserRole(undefined)).toEqual({ success: true, data: null });
      expect(await getUserRole('')).toEqual({ success: true, data: null });

      expect(mockDoc).not.toHaveBeenCalled();
      expect(mockGetDoc).not.toHaveBeenCalled();
    });

    it('returns valid staff role when user document has staff role', async () => {
      const mockUserDoc = {
        exists: () => true,
        data: () => ({ role: 'staff' })
      };

      mockGetDoc.mockResolvedValue(mockUserDoc);

      const result = await getUserRole('test-uid');

      expect(mockDoc).toHaveBeenCalledWith('mock-db-instance', 'users', 'test-uid');
      expect(mockGetDoc).toHaveBeenCalledWith('mock-doc-ref');
      expect(result).toEqual({ success: true, data: 'staff' });
    });

    it('returns valid closer role when user document has closer role', async () => {
      const mockUserDoc = {
        exists: () => true,
        data: () => ({ role: 'closer' })
      };

      mockGetDoc.mockResolvedValue(mockUserDoc);

      const result = await getUserRole('test-uid');

      expect(result).toEqual({ success: true, data: 'closer' });
    });

    it('returns valid viewer role when user document has viewer role', async () => {
      const mockUserDoc = {
        exists: () => true,
        data: () => ({ role: 'viewer' })
      };

      mockGetDoc.mockResolvedValue(mockUserDoc);

      const result = await getUserRole('test-uid');

      expect(result).toEqual({ success: true, data: 'viewer' });
    });

    it('returns success with null data for unknown roles and logs warning', async () => {
      const mockUserDoc = {
        exists: () => true,
        data: () => ({ role: 'unknown-role' })
      };

      mockGetDoc.mockResolvedValue(mockUserDoc);

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      const result = await getUserRole('test-uid');

      expect(result).toEqual({ success: true, data: null });
      expect(consoleSpy).toHaveBeenCalledWith('Unknown user role in Firestore:', 'unknown-role');

      consoleSpy.mockRestore();
    });

    it('returns success with null data when user document does not exist', async () => {
      const mockUserDoc = {
        exists: () => false
      };

      mockGetDoc.mockResolvedValue(mockUserDoc);

      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      const result = await getUserRole('test-uid');

      expect(result).toEqual({ success: true, data: null });
      expect(consoleSpy).toHaveBeenCalledWith("User test-uid has no matching user document.");

      consoleSpy.mockRestore();
    });

    it('returns error result when database operation fails', async () => {
      const mockError = new Error('Database connection failed');
      mockGetDoc.mockRejectedValue(mockError);

      const result = await getUserRole('test-uid');

      expect(result).toEqual({ success: false, data: null, error: 'Firestore connection failed' });
    });

    it('returns success with null data for missing role field in user document', async () => {
      const mockUserDoc = {
        exists: () => true,
        data: () => ({}) // No role field
      };

      mockGetDoc.mockResolvedValue(mockUserDoc);

      const result = await getUserRole('test-uid');

      expect(result).toEqual({ success: true, data: null });
    });

    it('returns success with null data for null role field in user document', async () => {
      const mockUserDoc = {
        exists: () => true,
        data: () => ({ role: null })
      };

      mockGetDoc.mockResolvedValue(mockUserDoc);

      const result = await getUserRole('test-uid');

      expect(result).toEqual({ success: true, data: null });
    });
  });
});

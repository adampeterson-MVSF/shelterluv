import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { getDogs, getDogById } from './dogRepository';
import { collection, getDocs, doc, getDoc } from 'firebase/firestore';
import { normalizeDog } from '../types/dogNormalize';

// Mock Firebase Firestore
vi.mock('firebase/firestore', () => ({
  collection: vi.fn(),
  getDocs: vi.fn(),
  doc: vi.fn(),
  getDoc: vi.fn()
}));

// Mock the app initialization
vi.mock('../app', () => ({
  db: {}
}));

// Mock normalizeDog
vi.mock('../types/dogNormalize', () => ({
  normalizeDog: vi.fn()
}));

describe('dogRepository', () => {
  let mockCollection;
  let mockGetDocs;
  let mockDoc;
  let mockGetDoc;
  let mockNormalizeDog;

  beforeEach(() => {
    mockCollection = vi.fn();
    mockGetDocs = vi.fn();
    mockDoc = vi.fn();
    mockGetDoc = vi.fn();
    mockNormalizeDog = vi.fn();

    collection.mockImplementation(mockCollection);
    getDocs.mockImplementation(mockGetDocs);
    doc.mockImplementation(mockDoc);
    getDoc.mockImplementation(mockGetDoc);
    normalizeDog.mockImplementation(mockNormalizeDog);

    // Reset mocks
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('getDogs', () => {
    it('fetches all dogs and normalizes them', async () => {
      const mockDogsSnapshot = {
        docs: [
          {
            id: 'dog1',
            data: () => ({ 'Internal-ID': '1', name: 'Dog 1' })
          },
          {
            id: 'dog2',
            data: () => ({ 'Internal-ID': '2', name: 'Dog 2' })
          }
        ]
      };

      const mockNormalizedDog1 = { id: '1', name: 'Dog 1' };
      const mockNormalizedDog2 = { id: '2', name: 'Dog 2' };

      mockCollection.mockReturnValue('mock-collection');
      mockGetDocs.mockResolvedValue(mockDogsSnapshot);
      mockNormalizeDog
        .mockReturnValueOnce(mockNormalizedDog1)
        .mockReturnValueOnce(mockNormalizedDog2);

      const result = await getDogs();

      expect(mockCollection).toHaveBeenCalledWith({}, 'dogs');
      expect(mockGetDocs).toHaveBeenCalledWith('mock-collection');
      expect(mockNormalizeDog).toHaveBeenCalledTimes(2);
      expect(result).toEqual({ success: true, data: [mockNormalizedDog1, mockNormalizedDog2] });
    });

    it('returns error when dog documents are malformed', async () => {
      const mockDogsSnapshot = {
        docs: [
          {
            id: 'dog1',
            data: () => ({ name: 'Dog 1' }) // Missing Internal-ID
          }
        ]
      };

      mockCollection.mockReturnValue('mock-collection');
      mockGetDocs.mockResolvedValue(mockDogsSnapshot);

      // Mock normalizeDog to throw for malformed documents
      mockNormalizeDog.mockImplementation(() => {
        throw new Error('missing required Internal-ID field');
      });

      const result = await getDogs();

      // Should return error since document is malformed
      expect(result).toEqual({
        success: false,
        error: 'missing required Internal-ID field',
        data: []
      });
    });

    it('handles firestore errors', async () => {
      const mockError = new Error('Firestore connection failed');
      mockCollection.mockReturnValue('mock-collection');
      mockGetDocs.mockRejectedValue(mockError);

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const result = await getDogs();

      expect(result).toEqual({ success: false, data: [], error: 'Firestore connection failed' });
      expect(consoleSpy).toHaveBeenCalledWith('Error fetching dogs from Firestore:', mockError);
      consoleSpy.mockRestore();
    });

    it('returns empty array when no dogs exist', async () => {
      const mockDogsSnapshot = {
        docs: []
      };

      mockCollection.mockReturnValue('mock-collection');
      mockGetDocs.mockResolvedValue(mockDogsSnapshot);

      const result = await getDogs();

      expect(result).toEqual({ success: true, data: [] });
    });

    it('returns error when any document has missing required ETL fields', async () => {
      const mockDogsSnapshot = {
        docs: [
          {
            id: 'dog1',
            data: () => ({
              'Internal-ID': '1',
              'ID': 'EXT-1',
              Name: 'Dog 1',
              Status: 'AVAILABLE'
              // Missing AgeYears, AgeDisplay, etc.
            })
          }
        ]
      };

      mockCollection.mockReturnValue('mock-collection');
      mockGetDocs.mockResolvedValue(mockDogsSnapshot);

      // Mock normalizeDog to throw for ETL contract violation
      mockNormalizeDog.mockImplementation(() => {
        throw new Error('Dog document dog1 missing ETL-required fields: AgeYears, AgeDisplay, IsInCustody, IsAvailableForAdoption, IsHospice, IsEventDog');
      });

      const result = await getDogs();

      expect(result).toEqual({
        success: false,
        error: 'Dog document dog1 missing ETL-required fields: AgeYears, AgeDisplay, IsInCustody, IsAvailableForAdoption, IsHospice, IsEventDog',
        data: []
      });
    });

  });

  describe('getDogById', () => {
    it('fetches a single dog and normalizes it', async () => {
      const mockDogDoc = {
        exists: () => true,
        id: 'dog1',
        data: () => ({ 'Internal-ID': '1', name: 'Dog 1' })
      };

      const mockNormalizedDog = { id: '1', name: 'Dog 1' };

      mockDoc.mockReturnValue('mock-doc-ref');
      mockGetDoc.mockResolvedValue(mockDogDoc);
      mockNormalizeDog.mockReturnValue(mockNormalizedDog);

      const result = await getDogById('dog1');

      expect(mockDoc).toHaveBeenCalledWith({}, 'dogs', 'dog1');
      expect(mockGetDoc).toHaveBeenCalledWith('mock-doc-ref');
      expect(mockNormalizeDog).toHaveBeenCalledWith(mockDogDoc);
      expect(result).toEqual({ success: true, data: mockNormalizedDog });
    });

    it('returns null when dog does not exist', async () => {
      const mockDogDoc = {
        exists: () => false
      };

      mockDoc.mockReturnValue('mock-doc-ref');
      mockGetDoc.mockResolvedValue(mockDogDoc);

      const result = await getDogById('nonexistent');

      expect(result).toEqual({ success: true, data: null });
      expect(mockNormalizeDog).not.toHaveBeenCalled();
    });

    it('returns error when existing dog document is malformed', async () => {
      const mockDogDoc = {
        exists: () => true,
        id: 'dog1',
        data: () => ({ name: 'Dog 1' }) // Missing Internal-ID
      };

      mockDoc.mockReturnValue('mock-doc-ref');
      mockGetDoc.mockResolvedValue(mockDogDoc);

      // Mock normalizeDog to throw for malformed documents
      mockNormalizeDog.mockImplementation(() => {
        throw new Error('missing required Internal-ID field');
      });

      const result = await getDogById('dog1');

      expect(result).toEqual({
        success: false,
        data: null,
        error: 'missing required Internal-ID field'
      });
    });

    it('handles firestore errors', async () => {
      const mockError = new Error('Firestore connection failed');
      mockDoc.mockReturnValue('mock-doc-ref');
      mockGetDoc.mockRejectedValue(mockError);

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      const result = await getDogById('dog1');

      expect(result).toEqual({ success: false, data: null, error: 'Firestore connection failed' });
      expect(consoleSpy).toHaveBeenCalledWith('Error fetching dog from Firestore:', mockError);
      consoleSpy.mockRestore();
    });

    it('returns error when existing dog document has missing required ETL fields', async () => {
      const mockDogDoc = {
        exists: () => true,
        id: 'dog1',
        data: () => ({
          'Internal-ID': '1',
          'ID': 'EXT-1',
          Name: 'Dog 1',
          Status: 'AVAILABLE'
          // Missing AgeYears, AgeDisplay, etc.
        })
      };

      mockDoc.mockReturnValue('mock-doc-ref');
      mockGetDoc.mockResolvedValue(mockDogDoc);

      // Mock normalizeDog to throw for ETL contract violation
      mockNormalizeDog.mockImplementation(() => {
        throw new Error('Dog document dog1 missing ETL-required fields: AgeYears, AgeDisplay, IsInCustody, IsAvailableForAdoption, IsHospice, IsEventDog');
      });

      const result = await getDogById('dog1');

      expect(result).toEqual({
        success: false,
        data: null,
        error: 'Dog document dog1 missing ETL-required fields: AgeYears, AgeDisplay, IsInCustody, IsAvailableForAdoption, IsHospice, IsEventDog'
      });
    });

  });
});

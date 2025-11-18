/**
 * @jest-environment jsdom
 */

import { normalizeDog } from '../dogNormalize.js';

describe('normalizeDog', () => {

  it('should normalize a complete dog document successfully', () => {
    const mockDoc = {
      id: 'test-dog-id',
      data: () => ({
        internalId: '12345',
        publicId: 'A001',
        name: 'Buddy',
        status: 'available',
        physical: {
          breed: 'Golden Retriever',
          ageDays: 1095, // 3 years
          sex: 'Male',
          sizeLabel: 'Large'
        },
        media: {
          photos: [],
          videos: []
        },
        attributes: {
          raw: []
        },
        medical: {
          microchips: []
        },
        content: {
          description: 'A friendly dog'
        },
        admin: {},
        source: {
          syncedAt: '2024-01-01T00:00:00.000Z'
        }
      })
    };

    const result = normalizeDog(mockDoc);

    expect(result).toMatchObject({
      id: 'test-dog-id',
      internalId: '12345',
      publicId: 'A001',
      name: 'Buddy',
      status: 'available',
      physical: {
        breed: 'Golden Retriever',
        ageDays: 1095,
        sex: 'Male',
        sizeLabel: 'Large'
      },
      media: {
        photos: [],
        videos: []
      },
      attributes: {
        raw: []
      },
      medical: {
        microchips: []
      },
      content: {
        description: 'A friendly dog'
      }
    });

    // Check computed display fields
    expect(result.primaryPhotoUrl).toBeNull();
    expect(result.ageDisplay).toBe('3 years');
    expect(result.statusDisplay).toMatchObject({
      text: 'Available',
      className: 'status-available'
    });
  });

  it('should throw error for missing internalId in all environments', () => {
    const mockDoc = {
      id: 'test-dog-id',
      data: () => ({
        // Missing internalId
        publicId: 'A001',
        name: 'Buddy'
      })
    };

    expect(() => normalizeDog(mockDoc)).toThrow(
      'Dog document test-dog-id missing required internalId field'
    );
  });

  it('should throw error for missing required ETL fields', () => {
    const mockDoc = {
      id: 'test-dog-id',
      data: () => ({
        internalId: '12345',
        publicId: 'A001',
        name: 'Buddy',
        // Missing required ETL fields
        physical: undefined
      })
    };

    expect(() => normalizeDog(mockDoc)).toThrow(
      'Dog document test-dog-id missing ETL-required fields: physical'
    );
  });

  it('should handle missing optional fields gracefully', () => {
    const mockDoc = {
      id: 'test-dog-id',
      data: () => ({
        internalId: '12345',
        publicId: 'A001',
        name: 'Buddy',
        status: 'available',
        physical: {
          ageDays: 730, // 2 years
          sex: 'Female'
        },
        media: {
          photos: [],
          videos: []
        },
        attributes: {
          raw: []
        },
        medical: {
          microchips: []
        },
        content: {
          description: ''
        },
        admin: {},
        source: {
          syncedAt: '2024-01-01T00:00:00.000Z'
        }
        // Missing optional fields like foster, location, etc.
      })
    };

    const result = normalizeDog(mockDoc);

    expect(result.foster).toBeUndefined();
    expect(result.location).toBeUndefined();
    expect(result.admin.adoptionFeeGroup).toBeUndefined();
  });
});

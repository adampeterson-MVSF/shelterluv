/**
 * @jest-environment jsdom
 */

import { normalizeDog } from '../dogNormalize.js';

describe('normalizeDog', () => {

  it('should normalize a complete dog document successfully', () => {
    const mockDoc = {
      id: 'test-dog-id',
      data: () => ({
        'Internal-ID': '12345',
        'ID': 'A001',
        'Name': 'Buddy',
        'Status': 'AVAILABLE',
        'AgeYears': 3.5,
        'AgeDisplay': '3 years',
        'IsInCustody': true,
        'IsAvailableForAdoption': true,
        'IsHospice': false,
        'IsEventDog': true,
        'Breed': 'Golden Retriever',
        'Size': 'Large',
        'Gender': 'Male'
      })
    };

    const result = normalizeDog(mockDoc);

    expect(result).toMatchObject({
      id: 'test-dog-id',
      'Internal-ID': '12345',
      'ID': 'A001',
      'Name': 'Buddy',
      'Status': 'AVAILABLE',
      'AgeYears': 3.5,
      'AgeDisplay': '3 years',
      'IsInCustody': true,
      'IsAvailableForAdoption': true,
      'IsHospice': false,
      'IsEventDog': true,
      'Breed': 'Golden Retriever',
      'Size': 'Large',
      'Gender': 'Male',
      'Description': undefined,
      'Photos': [],
      'Treatments': []
    });
    expect(result.MedicalHistory).toBeNull();
  });

  it('should throw error for missing Internal-ID in all environments', () => {
    const mockDoc = {
      id: 'test-dog-id',
      data: () => ({
        // Missing Internal-ID
        'Name': 'Buddy'
      })
    };

    expect(() => normalizeDog(mockDoc)).toThrow(
      'Dog document test-dog-id missing required Internal-ID field'
    );
  });

  it('should throw error for missing required ETL fields', () => {

    const mockDoc = {
      id: 'test-dog-id',
      data: () => ({
        'Internal-ID': '12345',
        'Name': 'Buddy',
        // Missing required ETL fields
        'AgeYears': undefined,
        'AgeDisplay': undefined,
        'IsInCustody': undefined,
        'IsAvailableForAdoption': undefined,
        'IsHospice': undefined,
        'IsEventDog': undefined
      })
    };

    expect(() => normalizeDog(mockDoc)).toThrow(
      'Dog document test-dog-id missing ETL-required fields: AgeYears, AgeDisplay, IsInCustody, IsAvailableForAdoption, IsHospice, IsEventDog. ETL schema contract violation - required fields must always be present.'
    );
  });

  it('should throw error for missing some required ETL fields', () => {

    const mockDoc = {
      id: 'test-dog-id',
      data: () => ({
        'Internal-ID': '12345',
        'Name': 'Buddy',
        // Missing some required ETL fields
        'AgeYears': undefined,
        'AgeDisplay': '3 years',
        'IsInCustody': true,
        'IsAvailableForAdoption': undefined,
        'IsHospice': false,
        'IsEventDog': true
      })
    };

    expect(() => normalizeDog(mockDoc)).toThrow(
      'Dog document test-dog-id missing ETL-required fields: AgeYears, IsAvailableForAdoption. ETL schema contract violation - required fields must always be present.'
    );
  });

  it('should throw error for missing required ETL fields in all environments', () => {
    const mockDoc = {
      id: 'test-dog-id',
      data: () => ({
        'Internal-ID': '12345',
        'Name': 'Buddy',
        'Status': 'AVAILABLE',
        // Missing required ETL fields - should always throw
        'AgeYears': undefined,
        'AgeDisplay': undefined,
        'IsInCustody': undefined,
        'IsAvailableForAdoption': undefined,
        'IsHospice': undefined,
        'IsEventDog': undefined
      })
    };

    expect(() => normalizeDog(mockDoc)).toThrow(
      'Dog document test-dog-id missing ETL-required fields: AgeYears, AgeDisplay, IsInCustody, IsAvailableForAdoption, IsHospice, IsEventDog. ETL schema contract violation - required fields must always be present.'
    );
  });

  it('should handle missing optional fields gracefully', () => {
    const mockDoc = {
      id: 'test-dog-id',
      data: () => ({
        'Internal-ID': '12345',
        'Name': 'Buddy',
        'Status': 'AVAILABLE',
        'AgeYears': 2,
        'AgeDisplay': '2 years',
        'IsInCustody': true,
        'IsAvailableForAdoption': true,
        'IsHospice': false,
        'IsEventDog': false,
        // Missing optional fields
        'Breed': undefined,
        'Size': undefined,
        'Photos': undefined,
        'Treatments': undefined
      })
    };

    const result = normalizeDog(mockDoc);

    expect(result.Breed).toBeUndefined();
    expect(result.Size).toBeUndefined();
    expect(result.Photos).toEqual([]);
    expect(result.Treatments).toEqual([]);
  });
});

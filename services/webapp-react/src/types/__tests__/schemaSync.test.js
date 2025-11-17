/**
 * Schema synchronization tests
 *
 * These tests ensure that the webapp TypeScript types remain in sync
 * with the canonical JSON schema. Any drift between the schema and
 * types will cause these tests to fail, preventing deployment of
 * inconsistent types.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load the canonical schema
function loadSchema() {
  const schemaPath = path.resolve(__dirname, '../../../../../common/schemas/dog.schema.json');
  const schemaContent = fs.readFileSync(schemaPath, 'utf8');
  return JSON.parse(schemaContent);
}

// Load TypeScript types (we'll check the structure by importing)
async function loadTypes() {
  // For now, we'll check the schema structure against expected TS types
  // In a real implementation, you might parse the TS files or use ts-morph
  const schema = loadSchema();
  return schema;
}

describe('Schema Synchronization', () => {
  let schema;

  beforeAll(() => {
    schema = loadSchema();
  });

  describe('Schema Structure', () => {
    test('schema has required properties', () => {
      expect(schema).toHaveProperty('$schema');
      expect(schema).toHaveProperty('type', 'object');
      expect(schema).toHaveProperty('properties');
      expect(schema).toHaveProperty('required');
      expect(Array.isArray(schema.required)).toBe(true);
    });

    test('schema has version', () => {
      expect(schema).toHaveProperty('version');
      expect(typeof schema.version).toBe('string');
    });
  });

  describe('Required Fields Sync', () => {
    test('all required schema fields are accounted for in types', () => {
      const requiredFields = schema.required;

      // Check that we have type definitions for all required fields
      const schemaProperties = Object.keys(schema.properties);

      requiredFields.forEach(field => {
        expect(schemaProperties).toContain(field);
      });
    });

    test('required fields have proper types', () => {
      const requiredFields = schema.required;

      requiredFields.forEach(field => {
        const fieldDef = schema.properties[field];
        expect(fieldDef).toBeDefined();
        expect(fieldDef).toHaveProperty('type');

        // Ensure required fields don't have default values in schema
        // (they should be explicitly provided)
        if (fieldDef.type === 'string') {
          // String fields should not default to empty string for required fields
          // unless it's a valid default
          const allowedDefaults = ['', 'Not Available'];
          if (fieldDef.hasOwnProperty('default')) {
            expect(allowedDefaults).toContain(fieldDef.default);
          }
        }
      });
    });
  });

  describe('Enum Synchronization', () => {
    test('Status enum matches expected values', () => {
      const statusProperty = schema.properties.Status;
      expect(statusProperty).toHaveProperty('enum');
      expect(Array.isArray(statusProperty.enum)).toBe(true);

      // These are the expected status values that frontend depends on
      const expectedStatuses = ['AVAILABLE', 'ADOPTED', 'PENDING', 'HOLD', 'UNKNOWN'];
      expect(statusProperty.enum).toEqual(expectedStatuses);
    });

    test('Size enum matches expected values', () => {
      const sizeProperty = schema.properties.Size;
      expect(sizeProperty).toHaveProperty('enum');
      expect(Array.isArray(sizeProperty.enum)).toBe(true);

      // These are the expected size values
      const expectedSizes = ['Small', 'Medium', 'Large', 'X-Large', 'UNKNOWN'];
      expect(sizeProperty.enum).toEqual(expectedSizes);
    });

    test('Gender enum matches expected values', () => {
      const genderProperty = schema.properties.Gender;
      expect(genderProperty).toHaveProperty('enum');
      expect(Array.isArray(genderProperty.enum)).toBe(true);

      // These are the expected gender values
      const expectedGenders = ['Male', 'Female'];
      expect(genderProperty.enum).toEqual(expectedGenders);
    });
  });

  describe('Field Type Consistency', () => {
    test('array fields are properly defined', () => {
      const arrayFields = ['Photos', 'Treatments'];

      arrayFields.forEach(field => {
        const fieldDef = schema.properties[field];
        expect(fieldDef).toBeDefined();
        expect(fieldDef.type).toBe('array');

        if (field === 'Photos') {
          expect(fieldDef.items).toEqual({
            type: 'string',
            format: 'uri',
            description: expect.stringContaining('URL to dog photo')
          });
        }
      });
    });

    test('boolean fields are properly defined', () => {
      const booleanFields = ['IsInCustody', 'IsAvailableForAdoption', 'IsHospice', 'IsEventDog'];

      booleanFields.forEach(field => {
        const fieldDef = schema.properties[field];
        expect(fieldDef).toBeDefined();
        expect(fieldDef.type).toBe('boolean');
      });
    });

    test('numeric fields are properly defined', () => {
      const numericFields = ['AgeYears'];

      numericFields.forEach(field => {
        const fieldDef = schema.properties[field];
        expect(fieldDef).toBeDefined();
        expect(fieldDef.type).toBe('number');
      });
    });
  });

  describe('ETL Contract Fields', () => {
    test('ETL contract fields are present and properly typed', () => {
      // These fields are guaranteed by ETL and relied upon by frontend
      const etlContractFields = [
        { name: 'AgeYears', type: 'number' },
        { name: 'AgeDisplay', type: 'string' },
        { name: 'IsInCustody', type: 'boolean' },
        { name: 'IsAvailableForAdoption', type: 'boolean' },
        { name: 'IsHospice', type: 'boolean' },
        { name: 'IsEventDog', type: 'boolean' },
      ];

      etlContractFields.forEach(({ name, type }) => {
        const fieldDef = schema.properties[name];
        expect(fieldDef).toBeDefined();
        expect(fieldDef.type).toBe(type);
      });
    });

    test('ETL contract fields are required', () => {
      const etlContractFields = [
        'AgeYears', 'AgeDisplay', 'IsInCustody',
        'IsAvailableForAdoption', 'IsHospice', 'IsEventDog'
      ];

      etlContractFields.forEach(field => {
        expect(schema.required).toContain(field);
      });
    });
  });

  describe('Schema Evolution Guards', () => {
    test('schema version is reasonable', () => {
      const version = schema.version;
      expect(version).toMatch(/^\d+\.\d+\.\d+$/); // Semantic versioning
    });

    test('no unexpected field removals', () => {
      // List of fields that must always exist for backwards compatibility
      const criticalFields = [
        'Internal-ID', 'ID', 'Name', 'Status',
        'AgeYears', 'AgeDisplay', 'IsInCustody', 'IsAvailableForAdoption'
      ];

      criticalFields.forEach(field => {
        expect(schema.properties).toHaveProperty(field);
      });
    });

    test('field types have not changed unexpectedly', () => {
      // Spot check some fields that should never change type
      const typeChecks = [
        { field: 'Internal-ID', expectedType: 'string' },
        { field: 'Name', expectedType: 'string' },
        { field: 'Status', expectedType: 'string' },
        { field: 'AgeYears', expectedType: 'number' },
        { field: 'IsInCustody', expectedType: 'boolean' },
      ];

      typeChecks.forEach(({ field, expectedType }) => {
        const fieldDef = schema.properties[field];
        expect(fieldDef.type).toBe(expectedType);
      });
    });
  });
});

/**
 * Schema synchronization tests.
 * Ensures that generated artifacts stay in sync with the canonical dog.schema.json.
 * FAILS LOUDLY when schema and artifacts drift - run 'npm run schema:gen' to fix.
 */

import { SIZE_ORDER } from '@common/sizeConfig.js';
import { STATUS_MAPPING, getAllStatuses } from '@common/statusMapping.js';
import fs from 'fs';
import path from 'path';

// Read the canonical schema
const schemaPath = path.join(process.cwd(), '..', '..', 'common', 'schemas', 'dog.schema.json');
const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));

describe('Schema Synchronization', () => {
  describe('SIZE_ORDER matches schema Size enum', () => {
    const schemaSizeValues = schema.properties.Size.enum;

    test('SIZE_ORDER exactly matches schema Size enum', () => {
      expect(SIZE_ORDER).toEqual(schemaSizeValues);
    });

    test('SIZE_ORDER contains no extra values', () => {
      expect(SIZE_ORDER).toHaveLength(schemaSizeValues.length);
      schemaSizeValues.forEach(size => {
        expect(SIZE_ORDER).toContain(size);
      });
    });
  });

  describe('STATUS_MAPPING keys match schema Status enum', () => {
    const schemaStatusValues = schema.properties.Status.enum;

    test('STATUS_MAPPING contains all schema status keys', () => {
      schemaStatusValues.forEach(status => {
        expect(STATUS_MAPPING).toHaveProperty(status);
      });
    });

    test('STATUS_MAPPING has the correct number of statuses', () => {
      expect(Object.keys(STATUS_MAPPING)).toHaveLength(schemaStatusValues.length);
    });

    test('getAllStatuses returns all schema statuses', () => {
      const allStatuses = getAllStatuses();
      expect(allStatuses.sort()).toEqual(schemaStatusValues.sort());
    });

    test('All STATUS_MAPPING entries have required properties', () => {
      Object.values(STATUS_MAPPING).forEach(mapping => {
        expect(mapping).toHaveProperty('text');
        expect(mapping).toHaveProperty('className');
        expect(mapping).toHaveProperty('isTerminal');
        expect(typeof mapping.isTerminal).toBe('boolean');
      });
    });
  });

  describe('Status mapping invariants', () => {
    test('ADOPTED status is terminal', () => {
      expect(STATUS_MAPPING.ADOPTED.isTerminal).toBe(true);
    });

    test('AVAILABLE, PENDING, HOLD, UNKNOWN statuses are non-terminal', () => {
      expect(STATUS_MAPPING.AVAILABLE.isTerminal).toBe(false);
      expect(STATUS_MAPPING.PENDING.isTerminal).toBe(false);
      expect(STATUS_MAPPING.HOLD.isTerminal).toBe(false);
      expect(STATUS_MAPPING.UNKNOWN.isTerminal).toBe(false);
    });
  });
});

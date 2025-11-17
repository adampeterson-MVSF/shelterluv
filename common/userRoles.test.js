/**
 * Tests for userRoles.js
 * Ensures roles match config.json and validation works correctly.
 */

const userRoles = require('./userRoles');
const config = require('./config.json');

describe('userRoles', () => {
  describe('VALID_ROLES and ROLES', () => {
    test('exports VALID_ROLES matching config.json roles', () => {
      expect(userRoles.VALID_ROLES).toEqual(config.roles);
      expect(userRoles.ROLES).toEqual(config.roles);
    });

    test('VALID_ROLES is an alias of ROLES', () => {
      expect(userRoles.VALID_ROLES).toBe(userRoles.ROLES);
    });

    test('contains expected roles', () => {
      const expectedRoles = ['viewer', 'closer', 'staff'];
      expect(userRoles.VALID_ROLES).toEqual(expect.arrayContaining(expectedRoles));
      expect(userRoles.VALID_ROLES.length).toBe(expectedRoles.length);
    });
  });

  describe('isValidRole', () => {
    test('returns true for valid roles', () => {
      expect(userRoles.isValidRole('viewer')).toBe(true);
      expect(userRoles.isValidRole('closer')).toBe(true);
      expect(userRoles.isValidRole('staff')).toBe(true);
    });

    test('returns false for invalid roles', () => {
      expect(userRoles.isValidRole('admin')).toBe(false);
      expect(userRoles.isValidRole('invalid')).toBe(false);
      expect(userRoles.isValidRole('')).toBe(false);
      expect(userRoles.isValidRole(null)).toBe(false);
      expect(userRoles.isValidRole(undefined)).toBe(false);
    });
  });

  describe('assertValidRole', () => {
    test('does not throw for valid roles', () => {
      expect(() => userRoles.assertValidRole('viewer')).not.toThrow();
      expect(() => userRoles.assertValidRole('closer')).not.toThrow();
      expect(() => userRoles.assertValidRole('staff')).not.toThrow();
    });

    test('throws for invalid roles', () => {
      expect(() => userRoles.assertValidRole('admin')).toThrow('Invalid role "admin"');
      expect(() => userRoles.assertValidRole('invalid')).toThrow('Invalid role "invalid"');
      expect(() => userRoles.assertValidRole('')).toThrow('Invalid role ""');
    });

    test('error message includes the invalid role', () => {
      try {
        userRoles.assertValidRole('bad-role');
        fail('Should have thrown');
      } catch (error) {
        expect(error.message).toContain('bad-role');
      }
    });
  });

  describe('isStaff', () => {
    test('returns true only for staff role', () => {
      expect(userRoles.isStaff('staff')).toBe(true);
    });

    test('returns false for non-staff roles', () => {
      expect(userRoles.isStaff('viewer')).toBe(false);
      expect(userRoles.isStaff('closer')).toBe(false);
      expect(userRoles.isStaff('admin')).toBe(false);
    });
  });

  describe('config.json sync', () => {
    test('roles in config.json match exported roles', () => {
      // This test ensures no hidden extra roles exist
      const configRoles = new Set(config.roles);
      const exportedRoles = new Set(userRoles.VALID_ROLES);

      expect(configRoles.size).toBe(exportedRoles.size);
      for (const role of configRoles) {
        expect(exportedRoles.has(role)).toBe(true);
      }
    });
  });
});


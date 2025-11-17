/**
 * Tests for adminInit.js
 * Ensures singleton enforcement and safety checks work correctly.
 * Tests fail-fast behavior when required env vars are missing.
 */

const adminInit = require('./adminInit');

describe('adminInit', () => {
  const ORIGINAL_ENV = process.env;

  beforeEach(() => {
    process.env = { ...ORIGINAL_ENV };
  });

  afterAll(() => {
    process.env = ORIGINAL_ENV;
  });

  test('exports expected functions', () => {
    expect(typeof adminInit.getAdminApp).toBe('function');
    expect(typeof adminInit.getAdminDb).toBe('function');
    expect(typeof adminInit.initializeAdmin).toBe('function');
  });

  test('fails fast when FIREBASE_PROJECT_ID is missing', () => {
    delete process.env.FIREBASE_PROJECT_ID;
    delete process.env.DEV_SCRIPTS_ENABLED;

    expect(() => {
      adminInit.initializeAdmin();
    }).toThrow();
  });

  test('fails fast when DEV_SCRIPTS_ENABLED is not set', () => {
    process.env.FIREBASE_PROJECT_ID = 'test-project';
    delete process.env.DEV_SCRIPTS_ENABLED;

    expect(() => {
      adminInit.initializeAdmin();
    }).toThrow(/DEV_SCRIPTS_ENABLED/);
  });

  test('fails fast when project is not safe', () => {
    process.env.FIREBASE_PROJECT_ID = 'muttville-prod';
    process.env.DEV_SCRIPTS_ENABLED = '1';

    expect(() => {
      adminInit.initializeAdmin();
    }).toThrow(/not safe/);
  });

  // Note: Testing actual Firebase Admin initialization requires proper env setup
  // Those tests belong in integration/e2e test suites, not unit tests
  // The singleton enforcement is tested implicitly by scripts that use adminInit
});

/**
 * Tests for firebaseConfig.js
 */

const { validateFirebaseEnv } = require('./firebaseConfig');
const { isProdProjectId, assertNotProdProject, ALLOWED_PROJECT_IDS } = require('./firebaseSafetyConfig');

// Mock process.env for testing
const originalEnv = { ...process.env };

describe('validateFirebaseEnv', () => {
  beforeEach(() => {
    // Reset process.env before each test
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    // Restore original process.env after each test
    process.env = originalEnv;
  });

  test('throws on missing FIREBASE_PROJECT_ID', () => {
    delete process.env.FIREBASE_PROJECT_ID;
    expect(() => validateFirebaseEnv()).toThrow('Missing required environment variable: FIREBASE_PROJECT_ID');
  });

  test('passes when FIREBASE_PROJECT_ID is present', () => {
    process.env.FIREBASE_PROJECT_ID = 'test-project';
    expect(() => validateFirebaseEnv()).not.toThrow();
  });
});

describe('assertNotProdProject', () => {
  test('allows whitelisted dev project', () => {
    expect(() => assertNotProdProject('dev-muttville')).not.toThrow();
  });

  test('allows whitelisted staging project', () => {
    expect(() => assertNotProdProject('staging-muttville')).not.toThrow();
  });

  test('allows whitelisted demo project', () => {
    expect(() => assertNotProdProject('muttville-demo')).not.toThrow();
  });

  test('throws on production project', () => {
    expect(() => assertNotProdProject('muttville-prod')).toThrow('is a production project');
  });

  test('throws on other production project', () => {
    expect(() => assertNotProdProject('muttville-production')).toThrow('is a production project');
  });

  test('throws on non-whitelisted project', () => {
    expect(() => assertNotProdProject('random-project')).toThrow('is not in the allowlist');
  });

  test('throws on empty project ID', () => {
    expect(() => assertNotProdProject('')).toThrow('No project ID provided');
  });
});

describe('firebaseSafetyConfig', () => {
  test('isProdProjectId identifies production projects', () => {
    expect(isProdProjectId('muttville-prod')).toBe(true);
    expect(isProdProjectId('muttville-production')).toBe(true);
    expect(isProdProjectId('some-prod-project')).toBe(false);
    expect(isProdProjectId('dev-muttville')).toBe(false);
  });

  test('assertNotProdProject allows whitelisted projects', () => {
    expect(() => assertNotProdProject('dev-muttville')).not.toThrow();
    expect(() => assertNotProdProject('staging-muttville')).not.toThrow();
    expect(() => assertNotProdProject('muttville-demo')).not.toThrow();
  });

  test('assertNotProdProject throws on production projects', () => {
    expect(() => assertNotProdProject('muttville-prod')).toThrow('is a production project');
    expect(() => assertNotProdProject('muttville-production')).toThrow('is a production project');
  });

  test('assertNotProdProject throws on non-whitelisted projects', () => {
    expect(() => assertNotProdProject('random-project')).toThrow('is not in the allowlist');
    expect(() => assertNotProdProject('')).toThrow('No project ID provided');
  });

  test('ALLOWED_PROJECT_IDS contains expected dev projects', () => {
    expect(ALLOWED_PROJECT_IDS).toContain('dev-muttville');
    expect(ALLOWED_PROJECT_IDS).toContain('staging-muttville');
    expect(ALLOWED_PROJECT_IDS).toContain('muttville-demo');
  });
});

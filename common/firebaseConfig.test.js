/**
 * Tests for firebaseConfig.js
 */

const {
  validateFirebaseAdminEnv,
  getFirebaseProjectId,
  getWebFirebaseConfigFromEnv
} = require('./firebaseConfig');
const { isProdProjectId, assertNotProdProject, ALLOWED_PROJECT_IDS } = require('./firebaseSafetyConfig');

// Mock process.env for testing
const originalEnv = { ...process.env };

describe('validateFirebaseAdminEnv', () => {
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
    expect(() => validateFirebaseAdminEnv()).toThrow('Missing required environment variable: FIREBASE_PROJECT_ID');
  });

  test('passes when FIREBASE_PROJECT_ID is present', () => {
    process.env.FIREBASE_PROJECT_ID = 'test-project';
    expect(() => validateFirebaseAdminEnv()).not.toThrow();
  });
});

describe('getFirebaseProjectId', () => {
  beforeEach(() => {
    // Reset process.env before each test
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    // Restore original process.env after each test
    process.env = originalEnv;
  });

  test('returns project ID when present', () => {
    process.env.FIREBASE_PROJECT_ID = 'test-project';
    expect(getFirebaseProjectId()).toBe('test-project');
  });

  test('throws when FIREBASE_PROJECT_ID is missing', () => {
    delete process.env.FIREBASE_PROJECT_ID;
    expect(() => getFirebaseProjectId()).toThrow('Missing required environment variable: FIREBASE_PROJECT_ID');
  });
});

describe('getWebFirebaseConfigFromEnv', () => {
  test('returns config object with all required VITE_ vars', () => {
    const mockEnv = {
      'VITE_FIREBASE_API_KEY': 'test-api-key',
      'VITE_FIREBASE_AUTH_DOMAIN': 'test.firebaseapp.com',
      'VITE_FIREBASE_PROJECT_ID': 'test-project',
      'VITE_FIREBASE_STORAGE_BUCKET': 'test.appspot.com',
      'VITE_FIREBASE_MESSAGING_SENDER_ID': '123456789',
      'VITE_FIREBASE_APP_ID': '1:123456789:web:abcdef'
    };

    const config = getWebFirebaseConfigFromEnv((key) => mockEnv[key]);

    expect(config).toEqual({
      firebase_api_key: 'test-api-key',
      firebase_auth_domain: 'test.firebaseapp.com',
      firebase_project_id: 'test-project',
      firebase_storage_bucket: 'test.appspot.com',
      firebase_messaging_sender_id: '123456789',
      firebase_app_id: '1:123456789:web:abcdef'
    });
  });

  test('throws on missing VITE_FIREBASE_API_KEY', () => {
    const mockEnv = {
      'VITE_FIREBASE_AUTH_DOMAIN': 'test.firebaseapp.com',
      // Missing VITE_FIREBASE_API_KEY
    };

    expect(() => getWebFirebaseConfigFromEnv((key) => mockEnv[key]))
      .toThrow('Missing required environment variable: VITE_FIREBASE_API_KEY');
  });

  test('uses process.env by default', () => {
    const originalEnv = { ...process.env };
    try {
      // Mock process.env
      process.env.VITE_FIREBASE_API_KEY = 'test-api-key';
      process.env.VITE_FIREBASE_AUTH_DOMAIN = 'test.firebaseapp.com';
      process.env.VITE_FIREBASE_PROJECT_ID = 'test-project';
      process.env.VITE_FIREBASE_STORAGE_BUCKET = 'test.appspot.com';
      process.env.VITE_FIREBASE_MESSAGING_SENDER_ID = '123456789';
      process.env.VITE_FIREBASE_APP_ID = '1:123456789:web:abcdef';

      const config = getWebFirebaseConfigFromEnv();

      expect(config.firebase_api_key).toBe('test-api-key');
      expect(config.firebase_project_id).toBe('test-project');
    } finally {
      process.env = originalEnv;
    }
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

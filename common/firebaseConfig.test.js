/**
 * Tests for firebaseConfig.js
 * Tests pure configuration helper functions.
 */

const {
  ensureProfile,
  getProjectId,
  getAdminProjectId,
  getEtlProjectId,
  getWebFirebaseConfigFromEnv
} = require('./firebaseConfig');

const ORIGINAL_ENV = process.env;

function resetEnv(overrides = {}) {
  process.env = {
    ...ORIGINAL_ENV,
    ...overrides
  };
}

describe('ensureProfile', () => {
  beforeEach(() => {
    resetEnv();
  });

  afterAll(() => {
    process.env = ORIGINAL_ENV;
  });

  test('passes when required admin env vars exist', () => {
    resetEnv({ FIREBASE_PROJECT_ID: 'test-project-123' });
    expect(() => ensureProfile('admin')).not.toThrow();
  });

  test('throws when required admin env vars are missing', () => {
    resetEnv({ FIREBASE_PROJECT_ID: undefined });
    expect(() => ensureProfile('admin')).toThrow('Missing required environment variables for admin profile: FIREBASE_PROJECT_ID');
  });

  test('passes when required web env vars exist', () => {
    resetEnv({
      FIREBASE_API_KEY: 'api-key',
      FIREBASE_AUTH_DOMAIN: 'domain',
      FIREBASE_PROJECT_ID: 'project',
      FIREBASE_STORAGE_BUCKET: 'bucket',
      FIREBASE_MESSAGING_SENDER_ID: 'sender',
      FIREBASE_APP_ID: 'app'
    });
    expect(() => ensureProfile('web')).not.toThrow();
  });

  test('throws when required web env vars are missing', () => {
    resetEnv({ FIREBASE_API_KEY: undefined });
    expect(() => ensureProfile('web')).toThrow(/Missing required environment variables for web profile/);
  });

  test('passes when required etl env vars exist', () => {
    resetEnv({
      SHELTERLUV_USER: 'user',
      SHELTERLUV_PASS: 'pass',
      SHELTERLUV_API_KEY: 'key',
      GCP_PROJECT: 'project',
      DOGS_COLLECTION: 'dogs'
    });
    expect(() => ensureProfile('etl')).not.toThrow();
  });

  test('throws when required etl env vars are missing', () => {
    resetEnv({ SHELTERLUV_USER: undefined });
    expect(() => ensureProfile('etl')).toThrow(/Missing required environment variables for etl profile/);
  });

  test('passes when required dev env vars exist', () => {
    resetEnv({ DEV_SCRIPTS_ENABLED: '1' });
    expect(() => ensureProfile('dev')).not.toThrow();
  });

  test('throws when required dev env vars are missing', () => {
    resetEnv({ DEV_SCRIPTS_ENABLED: undefined });
    expect(() => ensureProfile('dev')).toThrow(/Missing required environment variables for dev profile/);
  });

  test('error message mentions exact missing var names', () => {
    resetEnv({
      FIREBASE_API_KEY: 'key',
      // Missing FIREBASE_AUTH_DOMAIN and others
    });
    try {
      ensureProfile('web');
      fail('Should have thrown');
    } catch (error) {
      expect(error.message).toContain('FIREBASE_AUTH_DOMAIN');
      expect(error.message).toContain('FIREBASE_PROJECT_ID');
    }
  });
});

describe('getProjectId', () => {
  beforeEach(() => {
    resetEnv();
  });

  afterAll(() => {
    process.env = ORIGINAL_ENV;
  });

  test('returns admin project ID when set', () => {
    resetEnv({ FIREBASE_PROJECT_ID: 'test-project-123' });
    expect(getProjectId('admin')).toBe('test-project-123');
  });

  test('returns ETL project ID when set', () => {
    resetEnv({ GCP_PROJECT: 'etl-project-456' });
    expect(getProjectId('etl')).toBe('etl-project-456');
  });

  test('throws when FIREBASE_PROJECT_ID is not set for admin', () => {
    resetEnv({ FIREBASE_PROJECT_ID: undefined });
    expect(() => getProjectId('admin')).toThrow('Missing required environment variable: FIREBASE_PROJECT_ID');
  });

  test('throws when GCP_PROJECT is not set for ETL', () => {
    resetEnv({ GCP_PROJECT: undefined });
    expect(() => getProjectId('etl')).toThrow('Missing required environment variable: GCP_PROJECT');
  });

  test('throws for unknown profile', () => {
    expect(() => getProjectId('unknown')).toThrow('Profile \'unknown\' does not have a project ID');
  });
});

describe('getAdminProjectId', () => {
  beforeEach(() => {
    resetEnv();
  });

  afterAll(() => {
    process.env = ORIGINAL_ENV;
  });

  test('returns admin project ID when set', () => {
    resetEnv({ FIREBASE_PROJECT_ID: 'test-project-123' });
    expect(getAdminProjectId()).toBe('test-project-123');
  });

  test('throws when FIREBASE_PROJECT_ID is not set', () => {
    resetEnv({ FIREBASE_PROJECT_ID: undefined });
    expect(() => getAdminProjectId()).toThrow('Missing required environment variable: FIREBASE_PROJECT_ID');
  });

  test('works with custom env object', () => {
    const customEnv = { FIREBASE_PROJECT_ID: 'custom-admin-project' };
    expect(getAdminProjectId(customEnv)).toBe('custom-admin-project');
  });
});

describe('getEtlProjectId', () => {
  beforeEach(() => {
    resetEnv();
  });

  afterAll(() => {
    process.env = ORIGINAL_ENV;
  });

  test('returns ETL project ID when set', () => {
    resetEnv({ GCP_PROJECT: 'etl-project-456' });
    expect(getEtlProjectId()).toBe('etl-project-456');
  });

  test('throws when GCP_PROJECT is not set', () => {
    resetEnv({ GCP_PROJECT: undefined });
    expect(() => getEtlProjectId()).toThrow('Missing required environment variable: GCP_PROJECT');
  });

  test('works with custom env object', () => {
    const customEnv = { GCP_PROJECT: 'custom-etl-project' };
    expect(getEtlProjectId(customEnv)).toBe('custom-etl-project');
  });
});

describe('getWebFirebaseConfigFromEnv', () => {
  const baseWebEnv = {
    FIREBASE_API_KEY: 'api-key-123',
    FIREBASE_AUTH_DOMAIN: 'project.firebaseapp.com',
    FIREBASE_PROJECT_ID: 'project-id-456',
    FIREBASE_STORAGE_BUCKET: 'project.appspot.com',
    FIREBASE_MESSAGING_SENDER_ID: 'sender-789',
    FIREBASE_APP_ID: 'app-012'
  };

  beforeEach(() => {
    resetEnv(baseWebEnv);
  });

  afterAll(() => {
    process.env = ORIGINAL_ENV;
  });

  const makeGetEnv = (overrides = {}) => {
    const values = { ...baseWebEnv, ...overrides };
    return (key) => values[key];
  };

  test('returns config when all env vars are present', () => {
    const config = getWebFirebaseConfigFromEnv(makeGetEnv());

    expect(config).toEqual({
      apiKey: baseWebEnv.FIREBASE_API_KEY,
      authDomain: baseWebEnv.FIREBASE_AUTH_DOMAIN,
      projectId: baseWebEnv.FIREBASE_PROJECT_ID,
      storageBucket: baseWebEnv.FIREBASE_STORAGE_BUCKET,
      messagingSenderId: baseWebEnv.FIREBASE_MESSAGING_SENDER_ID,
      appId: baseWebEnv.FIREBASE_APP_ID
    });
  });

  test('throws when getEnv function is not provided', () => {
    expect(() => getWebFirebaseConfigFromEnv()).toThrow('getEnv function is required for webapp Firebase config');
  });

  test('throws when required env vars are missing after validation', () => {
    const getEnv = makeGetEnv({ FIREBASE_API_KEY: undefined });

    expect(() => getWebFirebaseConfigFromEnv(getEnv)).toThrow('Missing required environment variables for web profile: FIREBASE_API_KEY');
  });

  test('maps env var names to Firebase config keys', () => {
    const getEnv = makeGetEnv({
      FIREBASE_API_KEY: 'override-key',
      FIREBASE_AUTH_DOMAIN: 'override-domain'
    });

    const config = getWebFirebaseConfigFromEnv(getEnv);

    expect(config.apiKey).toBe('override-key');
    expect(config.authDomain).toBe('override-domain');
  });

  test('works with custom env object instead of process.env', () => {
    const customEnv = {
      FIREBASE_API_KEY: 'custom-api-key',
      FIREBASE_AUTH_DOMAIN: 'custom.firebaseapp.com',
      FIREBASE_PROJECT_ID: 'custom-project',
      FIREBASE_STORAGE_BUCKET: 'custom.appspot.com',
      FIREBASE_MESSAGING_SENDER_ID: 'custom-sender',
      FIREBASE_APP_ID: 'custom-app'
    };

    // Test ensureProfile with custom env
    expect(() => ensureProfile('web', customEnv)).not.toThrow();

    // Test getProjectId with custom env
    expect(getProjectId('admin', customEnv)).toBe('custom-project');

    // Test getWebFirebaseConfigFromEnv with Vite-style getEnv
    const viteGetEnv = (name) => customEnv[name];
    const config = getWebFirebaseConfigFromEnv(viteGetEnv, customEnv);

    expect(config.apiKey).toBe('custom-api-key');
    expect(config.authDomain).toBe('custom.firebaseapp.com');
    expect(config.projectId).toBe('custom-project');
  });

  test('does not accidentally hit real process.env when custom env provided', () => {
    // Set up real env with different values
    resetEnv({
      FIREBASE_API_KEY: 'real-env-key',
      FIREBASE_AUTH_DOMAIN: 'real.firebaseapp.com',
      FIREBASE_PROJECT_ID: 'real-project',
      FIREBASE_STORAGE_BUCKET: 'real.appspot.com',
      FIREBASE_MESSAGING_SENDER_ID: 'real-sender',
      FIREBASE_APP_ID: 'real-app'
    });

    // Use custom env with different values
    const customEnv = {
      FIREBASE_API_KEY: 'custom-key',
      FIREBASE_AUTH_DOMAIN: 'custom.firebaseapp.com',
      FIREBASE_PROJECT_ID: 'custom-project',
      FIREBASE_STORAGE_BUCKET: 'custom.appspot.com',
      FIREBASE_MESSAGING_SENDER_ID: 'custom-sender',
      FIREBASE_APP_ID: 'custom-app'
    };

    const viteGetEnv = (name) => customEnv[name];
    const config = getWebFirebaseConfigFromEnv(viteGetEnv, customEnv);

    // Should use custom env, not real process.env
    expect(config.apiKey).toBe('custom-key');
    expect(config.projectId).toBe('custom-project');
  });
});
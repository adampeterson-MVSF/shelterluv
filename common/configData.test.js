/**
 * Tests for configData.js
 * Ensures config structure validation and required keys.
 */

const fs = require('fs');
const path = require('path');
const {
  loadConfig,
  getEnvProfiles,
  getPythonEnvProfiles,
  getSafeProfiles,
  getRoles,
  getNormalizedProfileMap,
  getProjectSafetyMap,
  getCrossLanguageConfig,
  clearCache
} = require('./configData');

describe('configData', () => {
  const originalConfigPath = path.join(__dirname, 'config.json');
  let originalConfig;

  beforeEach(() => {
    // Save original config as string
    originalConfig = fs.readFileSync(originalConfigPath, 'utf8');
    clearCache();
  });

  afterEach(() => {
    // Restore original config from string
    fs.writeFileSync(originalConfigPath, originalConfig);
    clearCache();
  });

  // Helper to create invalid config by parsing and modifying
  function createInvalidConfig(modifier) {
    const config = JSON.parse(originalConfig);
    modifier(config);
    return config;
  }

  test('loads valid config successfully', () => {
    expect(() => loadConfig()).not.toThrow();
    const config = loadConfig();
    expect(config).toHaveProperty('env_profiles');
    expect(config).toHaveProperty('python_env_profiles');
    expect(config).toHaveProperty('safe_profiles');
    expect(config).toHaveProperty('roles');
  });

  test('throws when env_profiles is missing', () => {
    const invalidConfig = createInvalidConfig(config => {
      delete config.env_profiles;
    });
    fs.writeFileSync(originalConfigPath, JSON.stringify(invalidConfig, null, 2));
    clearCache();

    expect(() => loadConfig()).toThrow('config.json missing or invalid env_profiles object');
  });

  test('throws when python_env_profiles is missing', () => {
    const invalidConfig = createInvalidConfig(config => {
      delete config.python_env_profiles;
    });
    fs.writeFileSync(originalConfigPath, JSON.stringify(invalidConfig, null, 2));
    clearCache();

    expect(() => loadConfig()).toThrow('config.json missing or invalid python_env_profiles object');
  });

  test('throws when safe_profiles is missing', () => {
    const invalidConfig = createInvalidConfig(config => {
      delete config.safe_profiles;
    });
    fs.writeFileSync(originalConfigPath, JSON.stringify(invalidConfig, null, 2));
    clearCache();

    expect(() => loadConfig()).toThrow('config.json missing or invalid safe_profiles array');
  });

  test('throws when roles is missing', () => {
    const invalidConfig = createInvalidConfig(config => {
      delete config.roles;
    });
    fs.writeFileSync(originalConfigPath, JSON.stringify(invalidConfig, null, 2));
    clearCache();

    expect(() => loadConfig()).toThrow('config.json missing or invalid roles array');
  });

  test('throws when safe_profiles references missing python_env_profiles entry', () => {
    const invalidConfig = createInvalidConfig(config => {
      config.safe_profiles = ['nonexistent-profile'];
    });
    fs.writeFileSync(originalConfigPath, JSON.stringify(invalidConfig, null, 2));
    clearCache();

    expect(() => loadConfig()).toThrow(/safe_profiles includes "nonexistent-profile" but python_env_profiles/);
  });

  test('throws when safe_profile python_env_profiles entry missing gcp_project', () => {
    const invalidConfig = createInvalidConfig(config => {
      const firstSafeProfile = config.safe_profiles[0];
      config.python_env_profiles[firstSafeProfile] = {}; // Remove gcp_project
    });
    fs.writeFileSync(originalConfigPath, JSON.stringify(invalidConfig, null, 2));
    clearCache();

    expect(() => loadConfig()).toThrow(/gcp_project is missing or invalid/);
  });

  test('getEnvProfiles returns env_profiles', () => {
    const profiles = getEnvProfiles();
    expect(typeof profiles).toBe('object');
    expect(profiles).not.toBeNull();
  });

  test('getPythonEnvProfiles returns python_env_profiles', () => {
    const profiles = getPythonEnvProfiles();
    expect(typeof profiles).toBe('object');
    expect(profiles).not.toBeNull();
  });

  test('getSafeProfiles returns array', () => {
    const profiles = getSafeProfiles();
    expect(Array.isArray(profiles)).toBe(true);
    expect(profiles.length).toBeGreaterThan(0);
  });

  test('getRoles returns array', () => {
    const roles = getRoles();
    expect(Array.isArray(roles)).toBe(true);
    expect(roles.length).toBeGreaterThan(0);
  });

  test('caches config after first load', () => {
    const config1 = loadConfig();
    const config2 = loadConfig();
    expect(config1).toBe(config2); // Same object reference
  });

  test('clearCache clears cached config', () => {
    const config1 = loadConfig();
    clearCache();
    const config2 = loadConfig();
    expect(config1).not.toBe(config2); // Different object reference
  });

  test('throws when python_env_profiles entry has invalid gcp_project', () => {
    const invalidConfig = createInvalidConfig(config => {
      config.python_env_profiles.dev = { gcp_project: null }; // Invalid gcp_project
    });
    fs.writeFileSync(originalConfigPath, JSON.stringify(invalidConfig, null, 2));
    clearCache();

    expect(() => loadConfig()).toThrow(/python_env_profiles\.dev\.gcp_project is missing or invalid/);
  });

  test('throws when no production profiles exist', () => {
    const invalidConfig = createInvalidConfig(config => {
      // Make all python_env_profiles also safe_profiles (no production profiles)
      const allProfiles = Object.keys(config.python_env_profiles);
      config.safe_profiles = allProfiles;
    });
    fs.writeFileSync(originalConfigPath, JSON.stringify(invalidConfig, null, 2));
    clearCache();

    expect(() => loadConfig()).toThrow(/No production profiles found/);
  });

  test('validates safe_profiles and python_env_profiles consistency', () => {
    // This should pass with the original config
    expect(() => loadConfig()).not.toThrow();

    const config = loadConfig();
    const pythonProfileNames = Object.keys(config.python_env_profiles);
    const safeProfileNames = config.safe_profiles;

    // All safe profiles should have python_env_profiles entries (already tested above)
    // At least one profile should be production (not safe)
    const productionProfiles = pythonProfileNames.filter(name => !safeProfileNames.includes(name));
    expect(productionProfiles.length).toBeGreaterThan(0);
  });

  test('getNormalizedProfileMap returns stable profile->safety mappings', () => {
    const profileMap = getNormalizedProfileMap();
    expect(typeof profileMap).toBe('object');

    const config = loadConfig();
    const pythonProfiles = config.python_env_profiles;
    const safeProfiles = config.safe_profiles;

    // Should have entries for all python env profiles
    expect(Object.keys(profileMap)).toHaveLength(Object.keys(pythonProfiles).length);

    // Each entry should have gcp_project and is_safe properties
    for (const [profileName, profileData] of Object.entries(profileMap)) {
      expect(profileData).toHaveProperty('gcp_project');
      expect(typeof profileData.gcp_project).toBe('string');
      expect(profileData).toHaveProperty('is_safe');
      expect(typeof profileData.is_safe).toBe('boolean');

      // is_safe should match whether profile is in safe_profiles
      expect(profileData.is_safe).toBe(safeProfiles.includes(profileName));

      // gcp_project should match python_env_profiles
      expect(profileData.gcp_project).toBe(pythonProfiles[profileName].gcp_project);
    }

    // Golden snapshot: ensure stable mappings (this will fail if config changes intentionally)
    expect(profileMap).toMatchSnapshot();
  });

  test('getProjectSafetyMap returns stable project->profile mappings', () => {
    const projectMap = getProjectSafetyMap();
    expect(typeof projectMap).toBe('object');

    const config = loadConfig();
    const pythonProfiles = config.python_env_profiles;
    const safeProfiles = config.safe_profiles;

    // Should have entries for all unique GCP projects
    const expectedProjectCount = new Set(
      Object.values(pythonProfiles).map(p => p.gcp_project)
    ).size;
    expect(Object.keys(projectMap)).toHaveLength(expectedProjectCount);

    // Each entry should have env_profile_name and is_safe properties
    for (const [projectId, projectData] of Object.entries(projectMap)) {
      expect(projectData).toHaveProperty('env_profile_name');
      expect(typeof projectData.env_profile_name).toBe('string');
      expect(projectData).toHaveProperty('is_safe');
      expect(typeof projectData.is_safe).toBe('boolean');

      // is_safe should match whether the profile is in safe_profiles
      expect(projectData.is_safe).toBe(safeProfiles.includes(projectData.env_profile_name));

      // env_profile_name should be a valid profile that maps to this project
      const profileConfig = pythonProfiles[projectData.env_profile_name];
      expect(profileConfig).toBeDefined();
      expect(profileConfig.gcp_project).toBe(projectId);
    }

    // Golden snapshot: ensure stable mappings (this will fail if config changes intentionally)
    expect(projectMap).toMatchSnapshot();
  });

  test('fails loudly if someone deletes the last non-safe profile', () => {
    // This test ensures we never end up in an "all safe" scenario where there are no production profiles
    const config = loadConfig();
    const pythonProfileNames = Object.keys(config.python_env_profiles);
    const safeProfileNames = config.safe_profiles;

    const productionProfiles = pythonProfileNames.filter(name => !safeProfileNames.includes(name));

    // There must be at least one production profile
    expect(productionProfiles.length).toBeGreaterThan(0);

    // This is tested elsewhere too, but let's be explicit about the requirement
    expect(productionProfiles.length).toBeGreaterThan(0);
  });

  test('getCrossLanguageConfig returns machine-readable structure', () => {
    const crossLangConfig = getCrossLanguageConfig();
    expect(typeof crossLangConfig).toBe('object');

    const config = loadConfig();
    const pythonProfiles = config.python_env_profiles;
    const safeProfiles = config.safe_profiles;

    // Should have entries for all python env profiles
    expect(Object.keys(crossLangConfig)).toHaveLength(Object.keys(pythonProfiles).length);

    // Each entry should have gcp_project and is_safe properties
    for (const [profileName, profileData] of Object.entries(crossLangConfig)) {
      expect(profileData).toHaveProperty('gcp_project');
      expect(typeof profileData.gcp_project).toBe('string');
      expect(profileData).toHaveProperty('is_safe');
      expect(typeof profileData.is_safe).toBe('boolean');

      // is_safe should match whether profile is in safe_profiles
      expect(profileData.is_safe).toBe(safeProfiles.includes(profileName));

      // gcp_project should match python_env_profiles
      expect(profileData.gcp_project).toBe(pythonProfiles[profileName].gcp_project);
    }
  });
});


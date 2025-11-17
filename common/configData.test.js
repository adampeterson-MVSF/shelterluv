/**
 * Tests for configData.js (backward compatibility) and configArtifact.js
 * Tests the artifact data and accessors, not runtime parsing of config.json
 */

const {
  CONFIG_ARTIFACT,
  getEnvProfiles,
  getSafeProfiles,
  getRoles,
  getNormalizedProfileMap,
  getProjectSafetyMap,
  isProfileSafe,
  isProjectSafe
} = require('./configData');

describe('configData and configArtifact', () => {
  test('CONFIG_ARTIFACT has required structure', () => {
    expect(CONFIG_ARTIFACT).toHaveProperty('env_profiles');
    expect(CONFIG_ARTIFACT).toHaveProperty('safe_profiles');
    expect(CONFIG_ARTIFACT).toHaveProperty('roles');
    expect(CONFIG_ARTIFACT).toHaveProperty('profile_safety_map');
    expect(CONFIG_ARTIFACT).toHaveProperty('project_safety_map');
  });

  test('getEnvProfiles returns env_profiles', () => {
    const profiles = getEnvProfiles();
    expect(typeof profiles).toBe('object');
    expect(profiles).toHaveProperty('web');
    expect(profiles).toHaveProperty('admin');
    expect(profiles).toHaveProperty('etl');
    expect(profiles).toHaveProperty('dev');
  });

  test('getSafeProfiles returns array of safe profile names', () => {
    const profiles = getSafeProfiles();
    expect(Array.isArray(profiles)).toBe(true);
    expect(profiles.length).toBeGreaterThan(0);
    expect(profiles).toContain('dev');
    expect(profiles).toContain('staging');
  });

  test('getRoles returns array of valid roles', () => {
    const roles = getRoles();
    expect(Array.isArray(roles)).toBe(true);
    expect(roles.length).toBeGreaterThan(0);
    expect(roles).toContain('viewer');
    expect(roles).toContain('staff');
  });

  test('getNormalizedProfileMap returns profile safety mappings', () => {
    const profileMap = getNormalizedProfileMap();
    expect(typeof profileMap).toBe('object');

    // Should have entries for all profiles
    expect(Object.keys(profileMap)).toContain('dev');
    expect(Object.keys(profileMap)).toContain('prod');

    // Each entry should have gcp_project and is_safe properties
    for (const [profileName, profileData] of Object.entries(profileMap)) {
      expect(profileData).toHaveProperty('gcp_project');
      expect(typeof profileData.gcp_project).toBe('string');
      expect(profileData).toHaveProperty('is_safe');
      expect(typeof profileData.is_safe).toBe('boolean');
    }

    // Golden snapshot: ensure stable mappings
    expect(profileMap).toMatchSnapshot();
  });

  test('getProjectSafetyMap returns project safety mappings', () => {
    const projectMap = getProjectSafetyMap();
    expect(typeof projectMap).toBe('object');

    // Should have entries for all unique projects
    expect(Object.keys(projectMap)).toContain('dev-muttville');
    expect(Object.keys(projectMap)).toContain('muttville-prod');

    // Each entry should have is_safe property
    for (const [projectId, projectData] of Object.entries(projectMap)) {
      expect(projectData).toHaveProperty('is_safe');
      expect(typeof projectData.is_safe).toBe('boolean');
    }

    // Golden snapshot: ensure stable mappings
    expect(projectMap).toMatchSnapshot();
  });

  test('isProfileSafe correctly identifies safe profiles', () => {
    expect(isProfileSafe('dev')).toBe(true);
    expect(isProfileSafe('staging')).toBe(true);
    expect(isProfileSafe('prod')).toBe(false);
    expect(isProfileSafe('nonexistent')).toBe(false);
  });

  test('isProjectSafe correctly identifies safe projects', () => {
    expect(isProjectSafe('dev-muttville')).toBe(true);
    expect(isProjectSafe('staging-muttville')).toBe(true);
    expect(isProjectSafe('muttville-prod')).toBe(false);
    expect(isProjectSafe('nonexistent-project')).toBe(false);
  });

  test('artifact has at least one production profile', () => {
    const profileMap = CONFIG_ARTIFACT.profile_safety_map;
    const productionProfiles = Object.values(profileMap).filter(p => !p.is_safe);
    expect(productionProfiles.length).toBeGreaterThan(0);
  });

  test('all safe profiles have valid GCP projects', () => {
    const profileMap = CONFIG_ARTIFACT.profile_safety_map;
    const safeProfiles = CONFIG_ARTIFACT.safe_profiles;

    for (const profileName of safeProfiles) {
      expect(profileMap[profileName]).toBeDefined();
      expect(profileMap[profileName].gcp_project).toBeDefined();
      expect(typeof profileMap[profileName].gcp_project).toBe('string');
    }
  });
});


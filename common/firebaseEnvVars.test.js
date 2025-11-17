/**
 * Tests for firebaseEnvVars.js
 * Ensures ENV_PROFILES stays in sync with configArtifact.getEnvProfiles().
 */

const { getEnvProfiles } = require('./configArtifactHelpers');
const { ENV_PROFILES } = require('./firebaseEnvVars');

describe('firebaseEnvVars', () => {
  test('ENV_PROFILES matches configArtifact.getEnvProfiles()', () => {
    const configProfiles = getEnvProfiles();
    const envProfiles = ENV_PROFILES;

    // Check that all profiles match
    expect(Object.keys(envProfiles)).toEqual(Object.keys(configProfiles));

    // Check that each profile has the same structure
    for (const profileName of Object.keys(configProfiles)) {
      const configProfile = configProfiles[profileName];
      const envProfile = envProfiles[profileName];

      expect(envProfile).toBeDefined();
      expect(Array.isArray(envProfile.required)).toBe(true);
      expect(Array.isArray(envProfile.optional)).toBe(true);
      expect(Array.isArray(configProfile.required)).toBe(true);
      expect(Array.isArray(configProfile.optional)).toBe(true);

      // Check required vars match
      expect(envProfile.required).toEqual(configProfile.required);
      
      // Check optional vars match
      expect(envProfile.optional).toEqual(configProfile.optional);
    }
  });

  test('ENV_PROFILES is frozen (immutable)', () => {
    expect(() => {
      ENV_PROFILES.newProfile = { required: [], optional: [] };
    }).toThrow();
  });

  test('WEB_ENV_VARS exports correct vars', () => {
    const { WEB_ENV_VARS } = require('./firebaseEnvVars');
    const configWeb = getEnvProfiles().web;
    
    expect(WEB_ENV_VARS).toEqual(configWeb.required);
  });
});


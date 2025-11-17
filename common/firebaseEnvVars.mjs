/**
 * ES module version of environment variable definitions.
 * Single source of truth for required/optional environment variables per profile.
 */

const makeFrozenArray = (items) => Object.freeze([...items]);

export const ENV_PROFILES = Object.freeze({
  web: Object.freeze({
    required: makeFrozenArray([
      'FIREBASE_API_KEY',
      'FIREBASE_AUTH_DOMAIN',
      'FIREBASE_PROJECT_ID',
      'FIREBASE_STORAGE_BUCKET',
      'FIREBASE_MESSAGING_SENDER_ID',
      'FIREBASE_APP_ID'
    ]),
    optional: makeFrozenArray([])
  }),
  admin: Object.freeze({
    required: makeFrozenArray([
      'FIREBASE_PROJECT_ID'
    ]),
    optional: makeFrozenArray([])
  }),
  etl: Object.freeze({
    required: makeFrozenArray([
      'SHELTERLUV_USER',
      'SHELTERLUV_PASS',
      'SHELTERLUV_API_KEY',
      'GCP_PROJECT',
      'DOGS_COLLECTION'
    ]),
    optional: makeFrozenArray([
      'E2E_LIVE_DB',
      'DISABLE_SECRET_MANAGER'
    ])
  }),
  dev: Object.freeze({
    required: makeFrozenArray([
      'DEV_SCRIPTS_ENABLED'
    ]),
    optional: makeFrozenArray([])
  })
});

export const WEB_ENV_VARS = ENV_PROFILES.web.required;
export const ADMIN_ENV_VARS = ENV_PROFILES.admin.required;
export const ETL_ENV_VARS = ENV_PROFILES.etl.required;
export const DEV_ENV_VARS = ENV_PROFILES.dev.required;

export function getProfileEnvSpec(profile) {
  const spec = ENV_PROFILES[profile];
  if (!spec) {
    throw new Error(`Unknown profile: ${profile}. Use 'web', 'admin', 'etl', or 'dev'`);
  }
  return spec;
}

/**
 * Collect environment variables for a specific profile.
 * @param {string} profile - profile key
 * @param {Record<string, string | undefined>} [envSource] - environment source (defaults to process.env)
 * @returns {{required: readonly string[], optional: readonly string[], values: Record<string, string | undefined>, missing: string[], isValid: boolean}}
 */
export function collectProfileEnv(profile, envSource = process.env) {
  const spec = getProfileEnvSpec(profile);
  const values = {};

  for (const name of [...spec.required, ...spec.optional]) {
    values[name] = envSource[name];
  }

  const missing = spec.required.filter((varName) => !envSource[varName]);

  return {
    required: spec.required,
    optional: spec.optional,
    values,
    missing,
    isValid: missing.length === 0
  };
}

/**
 * Validate environment variables for a specific profile.
 * @param {string} profile - 'web', 'admin', 'etl', or 'dev'
 * @param {Record<string,string|undefined>} [envSource] - environment source (defaults to process.env)
 * @returns {{required: string[], optional: string[], missing: string[], isValid: boolean}}
 */
export function validateEnv(profile, envSource = process.env) {
  const { required, optional, missing, isValid } = collectProfileEnv(profile, envSource);
  return {
    required,
    optional,
    missing,
    isValid
  };
}
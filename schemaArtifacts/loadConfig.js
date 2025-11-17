/**
 * Schema loading and validation utilities.
 * Pure functions for loading and validating schema structure.
 */

const crypto = require('crypto');

/**
 * Canonical size ordering derived from schema.
 * Must match the order defined in the dog schema enum.
 */

/**
 * Generate MD5 checksum for content (first 8 chars).
 * @param {string} content - Raw content to checksum
 * @returns {string} 8-character hex checksum
 */
function generateChecksum(content) {
  return crypto.createHash('md5').update(content).digest('hex').substring(0, 8);
}

/**
 * Generate MD5 checksum for schema content (first 8 chars).
 * @param {string} schemaContent - Raw JSON schema file content
 * @returns {string} 8-character hex checksum
 */
function generateSchemaChecksum(schemaContent) {
  return generateChecksum(schemaContent);
}

/**
 * Generate MD5 checksum for config content (first 8 chars).
 * @param {string} configContent - Raw JSON config file content
 * @returns {string} 8-character hex checksum
 */
function generateConfigChecksum(configContent) {
  return generateChecksum(configContent);
}

/**
 * Assert that schema has required structure for artifact generation.
 * @param {object} schema - Parsed JSON schema object
 * @param {string} [schemaPath='common/schemas/dog.schema.json'] - Path to schema file for error messages
 * @throws {Error} If schema structure is invalid
 */
function assertSchemaStructure(schema, schemaPath = 'common/schemas/dog.schema.json') {
  if (!schema || typeof schema !== 'object') {
    throw new Error(`Schema validation failed (${schemaPath}): schema must be an object`);
  }

  if (!Array.isArray(schema.required)) {
    throw new Error(`Schema validation failed (${schemaPath}): schema.required must be an array`);
  }

  if (!schema.properties || typeof schema.properties !== 'object') {
    throw new Error(`Schema validation failed (${schemaPath}): schema.properties must be an object`);
  }

  const status = schema.properties.Status;
  if (!status || !Array.isArray(status.enum)) {
    throw new Error(`Schema validation failed (${schemaPath}): Status.enum must be an array. Found: ${typeof status?.enum}`);
  }

  if (!Array.isArray(status['x-terminal-statuses'])) {
    throw new Error(`Schema validation failed (${schemaPath}): Status.x-terminal-statuses must be an array. Found: ${typeof status['x-terminal-statuses']}`);
  }

  const size = schema.properties.Size;
  if (!size || !Array.isArray(size.enum)) {
    throw new Error(`Schema validation failed (${schemaPath}): Size.enum must be an array. Found: ${typeof size?.enum}`);
  }
}

/**
 * Enumerate valid status values from schema.
 * @param {object} schema - Parsed JSON schema object
 * @returns {string[]} Array of valid status values
 */
function enumerateStatuses(schema) {
  return schema.properties.Status.enum || [];
}

/**
 * Enumerate valid size values from schema.
 * @param {object} schema - Parsed JSON schema object
 * @returns {string[]} Array of valid size values
 */
function enumerateSizes(schema) {
  return schema.properties.Size.enum || [];
}

/**
 * Get required fields from schema.
 * @param {object} schema - Parsed JSON schema object
 * @returns {string[]} Array of required field names
 */
function enumerateRequiredFields(schema) {
  return schema.required || [];
}

/**
 * Enumerate field ownership metadata from schema.
 * @param {object} schema - Parsed JSON schema object
 * @returns {object} Object mapping field names to ownership info { ownership: string, group: string }
 */
function enumerateFieldOwnership(schema) {
  const ownership = {};
  for (const [fieldName, fieldDef] of Object.entries(schema.properties)) {
    ownership[fieldName] = {
      ownership: fieldDef['x-ownership'] || 'unknown',
      group: fieldDef['x-group'] || 'unknown'
    };
  }
  return ownership;
}

/**
 * Get terminal statuses from schema.
 * @param {object} schema - Parsed JSON schema object
 * @returns {string[]} Array of terminal status values
 */
function enumerateTerminalStatuses(schema) {
  return schema.properties.Status['x-terminal-statuses'] || [];
}

/**
 * Get size ordering derived from schema enum order.
 * @param {object} schema - Parsed JSON schema object
 * @returns {string[]} Array of size values in canonical order
 */
function getSizeOrdering(schema) {
  return schema.properties.Size.enum || [];
}

/**
 * Extract comprehensive schema metadata for artifact generation.
 * @param {object} schema - Parsed JSON schema object
 * @returns {object} Schema metadata object
 */
function extractSchemaMetadata(schema) {
  return {
    requiredFields: enumerateRequiredFields(schema),
    statuses: enumerateStatuses(schema),
    sizes: enumerateSizes(schema),
    terminalStatuses: enumerateTerminalStatuses(schema),
    sizeOrdering: getSizeOrdering(schema),
    fieldOwnership: enumerateFieldOwnership(schema)
  };
}

module.exports = {
  generateChecksum,
  generateSchemaChecksum,
  generateConfigChecksum,
  assertSchemaStructure,
  enumerateStatuses,
  enumerateSizes,
  enumerateRequiredFields,
  enumerateFieldOwnership,
  enumerateTerminalStatuses,
  getSizeOrdering,
  extractSchemaMetadata
};

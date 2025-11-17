/**
 * Schema loading and validation utilities.
 * Pure functions for loading and validating schema structure.
 */

const crypto = require('crypto');

/**
 * Generate MD5 checksum for schema content (first 8 chars).
 * @param {string} schemaContent - Raw JSON schema file content
 * @returns {string} 8-character hex checksum
 */
function generateSchemaChecksum(schemaContent) {
  return crypto.createHash('md5').update(schemaContent).digest('hex').substring(0, 8);
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

module.exports = {
  generateSchemaChecksum,
  assertSchemaStructure,
  enumerateStatuses,
  enumerateSizes
};

/**
 * Schema-related utilities and artifacts.
 * Single source for schema reading, validation, and artifact sync checks.
 */

const fs = require('fs');
const path = require('path');

let cachedSchema = null;

/**
 * Get parsed dog schema, cached for performance.
 * @returns {object} Parsed JSON schema object
 */
function getDogSchema() {
  if (cachedSchema) {
    return cachedSchema;
  }

  const schemaPath = path.join(__dirname, 'schemas', 'dog.schema.json');
  const schemaContent = fs.readFileSync(schemaPath, 'utf8');
  cachedSchema = JSON.parse(schemaContent);
  return cachedSchema;
}

/**
 * Get required fields from dog schema for validation.
 * @returns {string[]} Array of required field names
 */
function getRequiredFieldsFromSchema() {
  const schema = getDogSchema();
  return schema.required || [];
}

/**
 * Get terminal statuses from dog schema.
 * Terminal statuses indicate dogs that are no longer available for adoption.
 * @returns {string[]} Array of terminal status values
 */
function getTerminalStatuses() {
  const schema = getDogSchema();
  return schema.properties.Status['x-terminal-statuses'] || [];
}

/**
 * Assert that schema artifacts are in sync with the canonical schema.
 * Call this in CI or at startup to ensure generated artifacts match schema.
 * @throws {Error} If any artifacts are out of sync
 */
function assertSchemaArtifactsInSync() {
  // Read schema file content the same way as generation script
  const schemaPath = path.join(__dirname, 'schemas', 'dog.schema.json');
  const schemaContent = fs.readFileSync(schemaPath, 'utf8');
  const schema = JSON.parse(schemaContent);

  // Runtime schema sanity checks
  if (!Array.isArray(schema.required)) {
    throw new Error('Schema validation failed: schema.required must be an array');
  }
  if (!schema.properties || typeof schema.properties !== 'object') {
    throw new Error('Schema validation failed: schema.properties must be an object');
  }
  if (!schema.properties.Status || !schema.properties.Status['x-terminal-statuses'] || !Array.isArray(schema.properties.Status['x-terminal-statuses'])) {
    throw new Error('Schema validation failed: Status.x-terminal-statuses must be an array');
  }

  // Check generated artifacts exist and are in sync
  const artifacts = [
    { file: 'statusMapping.js', description: 'Status display mappings' },
    { file: 'sizeConfig.js', description: 'Size category configuration' }
  ];

  for (const artifact of artifacts) {
    try {
      const artifactPath = path.join(__dirname, artifact.file);
      const content = fs.readFileSync(artifactPath, 'utf8');

      // Extract checksum from header comment (for JS files)
      if (artifact.file.endsWith('.js')) {
        const checksumMatch = content.match(/Schema checksum: ([a-f0-9]{8})/);
        if (!checksumMatch) {
          throw new Error(`${artifact.file} missing schema checksum in header`);
        }

        const expectedChecksum = generateSchemaChecksum(schemaContent);
        if (checksumMatch[1] !== expectedChecksum) {
          throw new Error(`${artifact.file} out of sync. Expected checksum: ${expectedChecksum}, found: ${checksumMatch[1]}`);
        }
      } else {
        // For JSON files, just validate they're parseable
        JSON.parse(content);
      }
    } catch (error) {
      if (error.code === 'ENOENT') {
        throw new Error(`${artifact.file} not found - run "npm run schema:gen" to generate`);
      }
      throw error;
    }
  }
}

/**
 * Generate a short checksum of schema content for version tracking.
 * @param {string} schemaContent - Stringified schema content
 * @returns {string} 8-character hex checksum
 */
function generateSchemaChecksum(schemaContent) {
  const crypto = require('crypto');
  return crypto.createHash('md5').update(schemaContent).digest('hex').substring(0, 8);
}

module.exports = {
  getDogSchema,
  getRequiredFieldsFromSchema,
  getTerminalStatuses,
  assertSchemaArtifactsInSync,
  generateSchemaChecksum
};

/**
 * Read-only schema access layer.
 * Pure functions for accessing dog schema data.
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
 * Get status enum values from schema.
 * @returns {string[]} Array of valid status values
 */
function getStatusEnums() {
  const schema = getDogSchema();
  return schema.properties.Status.enum || [];
}

/**
 * Get size enum values from schema.
 * @returns {string[]} Array of valid size values
 */
function getSizeEnums() {
  const schema = getDogSchema();
  return schema.properties.Size.enum || [];
}

module.exports = {
  getDogSchema,
  getStatusEnums,
  getSizeEnums
};

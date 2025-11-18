/**
 * Schema artifact generation functions.
 * Pure functions for generating artifacts from schema and config.
 */

const { assertSchemaStructure, generateSchemaChecksum, enumerateStatuses, enumerateSizes, enumerateRequiredFields, enumerateFieldOwnership, enumerateTerminalStatuses, getSizeOrdering, extractSchemaMetadata } = require('./loadConfig');
const { generateStatusMapping, generateSizeConfig, generateDogTypesHeader, generatePythonDogTypes, generateConfigArtifact, generatePythonConfigArtifact, generateSchemaArtifact, generatePythonSchemaArtifact } = require('./transformSchema');
const { generateTypescriptDogTypes } = require('./generateTypes');

/**
 * Generate all schema artifacts from a single schema load.
 * Pure function - parses schema once and generates all outputs.
 * @param {string} schemaContent - Raw JSON schema file content
 * @param {object} options - Options object
 * @param {string} [options.schemaPath='common/schemas/dog.schema.json'] - Path to schema file for error messages
 * @param {string} [options.generatorFileName='generators.js'] - Name of generator file
 * @returns {object} Object with statusMapping, sizeConfig, dogTypesHeader strings
 * @throws {Error} If schema is invalid or structure doesn't match expectations
 */
function generateAllArtifacts(schemaContent, options = {}) {
  const { schemaPath = 'common/schemas/dog.schema.json' } = options;

  let schema;
  try {
    schema = JSON.parse(schemaContent);
  } catch (error) {
    throw new Error(`Failed to parse schema JSON (${schemaPath}): ${error.message}`);
  }

  assertSchemaStructure(schema, schemaPath);

  return {
    statusMapping: generateStatusMapping(schema, schemaContent),
    sizeConfig: generateSizeConfig(schema, schemaContent),
    dogTypesHeader: generateDogTypesHeader(schemaContent, options),
    typescriptDogTypes: generateTypescriptDogTypes(schema, schemaContent),
    pythonDogTypes: generatePythonDogTypes(schema, schemaContent)
  };
}

/**
 * Generate config artifact from config.json.
 * Pure function - validates config and generates normalized artifact.
 * @param {string} configContent - Raw JSON config file content
 * @param {object} options - Options object
 * @param {string} [options.configPath='common/config.json'] - Path to config file for error messages
 * @returns {string} Generated config artifact content
 * @throws {Error} If config is invalid
 */
function generateConfigArtifactFromContent(configContent, options = {}) {
  const { configPath = 'common/config.json' } = options;

  let config;
  try {
    config = JSON.parse(configContent);
  } catch (error) {
    throw new Error(`Failed to parse config JSON (${configPath}): ${error.message}`);
  }

  return generateConfigArtifact(config, configContent);
}

/**
 * Generate Python config artifact from config.json.
 * Pure function - validates config and generates Python module.
 * @param {string} configContent - Raw JSON config file content
 * @param {object} options - Options object
 * @param {string} [options.configPath='common/config.json'] - Path to config file for error messages
 * @returns {string} Generated Python config artifact content
 * @throws {Error} If config is invalid
 */
function generatePythonConfigArtifactFromContent(configContent, options = {}) {
  const { configPath = 'common/config.json' } = options;

  let config;
  try {
    config = JSON.parse(configContent);
  } catch (error) {
    throw new Error(`Failed to parse config JSON (${configPath}): ${error.message}`);
  }

  return generatePythonConfigArtifact(config, configContent);
}

/**
 * Generate complete artifact bundle with checksum.
 * Single function that returns all artifacts and metadata in one object.
 * Use this when you need the checksum along with all generated artifacts.
 * @param {string} schemaContent - Raw JSON schema file content
 * @param {object} options - Options object
 * @param {string} [options.schemaPath='common/schemas/dog.schema.json'] - Path to schema file for error messages
 * @param {string} [options.generatorFileName='generators.js'] - Name of generator file
 * @returns {object} Object with checksum, statusMapping, sizeConfig, dogTypesHeader, and status/size arrays
 * @throws {Error} If schema is invalid or structure doesn't match expectations
 */
function generateArtifactBundle(schemaContent, options = {}) {
  const { schemaPath = 'common/schemas/dog.schema.json' } = options;

  let schema;
  try {
    schema = JSON.parse(schemaContent);
  } catch (error) {
    throw new Error(`Failed to parse schema JSON (${schemaPath}): ${error.message}`);
  }

  assertSchemaStructure(schema, schemaPath);

  const checksum = generateSchemaChecksum(schemaContent);
  const artifacts = generateAllArtifacts(schemaContent, options);

  return {
    checksum,
    statusMapping: artifacts.statusMapping,
    sizeConfig: artifacts.sizeConfig,
    dogTypesHeader: artifacts.dogTypesHeader,
    pythonDogTypes: artifacts.pythonDogTypes,
    statuses: enumerateStatuses(schema),
    sizes: enumerateSizes(schema)
  };
}

module.exports = {
  generateAllArtifacts,
  generateArtifactBundle,
  generateConfigArtifactFromContent,
  generatePythonConfigArtifactFromContent
};

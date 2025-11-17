/**
 * Core schema artifact generation logic.
 * Now delegates to focused modules for better organization.
 */

const { generateSchemaChecksum, assertSchemaStructure, enumerateStatuses, enumerateSizes } = require('./schemaArtifacts/loadConfig');
const { generateStatusMapping, generateSizeConfig, generateDogTypesHeader, generatePythonDogTypes, jsonTypeToPythonType } = require('./schemaArtifacts/transformSchema');
const { generateAllArtifacts, generateArtifactBundle } = require('./schemaArtifacts/writers');

const DEFAULT_SIZE_ORDER = ['Small', 'Medium', 'Large', 'X-Large', 'UNKNOWN'];


module.exports = {
  assertSchemaStructure,
  generateSchemaChecksum,
  generateStatusMapping,
  generateSizeConfig,
  generateDogTypesHeader,
  generatePythonDogTypes,
  jsonTypeToPythonType,
  generateAllArtifacts,
  generateArtifactBundle,
  enumerateStatuses,
  enumerateSizes,
  DEFAULT_SIZE_ORDER
};


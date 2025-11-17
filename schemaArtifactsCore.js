/**
 * Core schema artifact generation logic.
 * Now delegates to focused modules for better organization.
 */

const { generateSchemaChecksum, assertSchemaStructure, enumerateStatuses, enumerateSizes } = require('./schemaArtifacts/loadConfig');
const { generateStatusMapping, generateSizeConfig, generateDogTypesHeader, generatePythonDogTypes, jsonTypeToPythonType } = require('./schemaArtifacts/transformSchema');
const { generateAllArtifacts, generateArtifactBundle } = require('./schemaArtifacts/writers');


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
  enumerateSizes
};


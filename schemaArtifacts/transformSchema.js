/**
 * Schema transformation utilities.
 * Orchestrator for generating all artifacts from schema and config data.
 */

const { generateStatusMapping, generateSizeConfig } = require('./generateDogArtifacts');
const { generateTypescriptDogTypes, generatePythonDogTypes, generateDogTypesHeader } = require('./generateTypes');
const { generateConfigArtifact, generatePythonConfigArtifact } = require('./generateConfigArtifacts');

// Stub functions for schema artifacts - TODO: implement properly
function generateSchemaArtifact(schema, schemaContent, options = {}) {
  throw new Error('generateSchemaArtifact not yet implemented in refactored code');
}

function generatePythonSchemaArtifact(schema, schemaContent, options = {}) {
  throw new Error('generatePythonSchemaArtifact not yet implemented in refactored code');
}

// Re-export functions from sub-modules for backward compatibility
module.exports = {
  generateStatusMapping,
  generateSizeConfig,
  generateDogTypesHeader,
  generateTypescriptDogTypes,
  generatePythonDogTypes,
  generateConfigArtifact,
  generatePythonConfigArtifact,
  generateSchemaArtifact,
  generatePythonSchemaArtifact
};

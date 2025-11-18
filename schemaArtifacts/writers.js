/**
 * Schema artifact writers and orchestration.
 * High-level functions for generating and bundling artifacts.
 * This module re-exports functions from specialized modules for backward compatibility.
 */

const { ARTIFACT_PATHS } = require('./paths');
const { generateAllArtifacts, generateArtifactBundle, generateConfigArtifactFromContent, generatePythonConfigArtifact } = require('./generators');
const { writeArtifactsToDisk, updateTypescriptTypesHeader, checkArtifactsSync } = require('./io');

module.exports = {
  ARTIFACT_PATHS,
  generateAllArtifacts,
  generateArtifactBundle,
  generateConfigArtifactFromContent,
  generatePythonConfigArtifact,
  writeArtifactsToDisk,
  updateTypescriptTypesHeader,
  checkArtifactsSync
};

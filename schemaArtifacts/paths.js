/**
 * Schema artifact file paths configuration.
 * Canonical list of all generated artifact files.
 */

/**
 * Canonical list of all generated artifact files.
 * Used by both writeArtifactsToDisk and checkArtifactsSync to ensure consistency.
 */
const ARTIFACT_PATHS = {
  schemaArtifact: 'common/schemaArtifact.js',
  pythonSchemaArtifact: 'services/etl_scraper_py/schema_artifact.py',
  configArtifact: 'common/configArtifact.js',
  pythonConfigArtifact: 'services/etl_scraper_py/config_artifact.py',
  statusMapping: 'common/statusMapping.js',
  sizeConfig: 'common/sizeConfig.js',
  pythonDogTypes: 'services/etl_scraper_py/dog_types.py',
  dogTypes: 'services/webapp-react/src/types/Dog.types.ts'
};

module.exports = {
  ARTIFACT_PATHS
};

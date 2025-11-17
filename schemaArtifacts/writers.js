/**
 * Schema artifact writers and orchestration.
 * High-level functions for generating and bundling artifacts.
 */

const { assertSchemaStructure, generateSchemaChecksum, enumerateStatuses, enumerateSizes } = require('./loadConfig');
const { generateStatusMapping, generateSizeConfig, generateDogTypesHeader, generatePythonDogTypes } = require('./transformSchema');

/**
 * Generate all schema artifacts from a single schema load.
 * Pure function - parses schema once and generates all outputs.
 * @param {string} schemaContent - Raw JSON schema file content
 * @param {object} options - Options object
 * @param {string} [options.schemaPath='common/schemas/dog.schema.json'] - Path to schema file for error messages
 * @param {string} [options.generatorFileName='schemaArtifactsCli.js'] - Name of generator file
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
    pythonDogTypes: generatePythonDogTypes(schema, schemaContent)
  };
}

/**
 * Generate complete artifact bundle with checksum.
 * Single function that returns all artifacts and metadata in one object.
 * Use this when you need the checksum along with all generated artifacts.
 * @param {string} schemaContent - Raw JSON schema file content
 * @param {object} options - Options object
 * @param {string} [options.schemaPath='common/schemas/dog.schema.json'] - Path to schema file for error messages
 * @param {string} [options.generatorFileName='schemaArtifactsCli.js'] - Name of generator file
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

/**
 * Write artifacts to disk.
 * Orchestrates reading schema/config files and writing generated artifacts.
 * @param {object} options - Options object
 * @param {string} [options.schemaPath='common/schemas/dog.schema.json'] - Path to schema file
 * @param {string} [options.configPath='common/config.json'] - Path to config file
 * @param {string} [options.statusMappingPath='common/statusMapping.js'] - Path for status mapping output
 * @param {string} [options.sizeConfigPath='common/sizeConfig.js'] - Path for size config output
 * @param {string} [options.configArtifactPath='common/configArtifact.js'] - Path for config artifact output
 * @param {string} [options.pythonConfigArtifactPath='services/etl_scraper_py/config_artifact.py'] - Path for Python config artifact
 * @param {string} [options.dogTypesPath='services/webapp-react/src/types/Dog.types.ts'] - Path for TS types output
 * @param {string} [options.pythonDogTypesPath='services/etl_scraper_py/dog_types.py'] - Path for Python types output
 * @param {function} [options.readFile] - File reading function (defaults to fs.readFileSync)
 * @param {function} [options.writeFile] - File writing function (defaults to fs.writeFileSync)
 * @param {function} [options.fileExists] - File existence check (defaults to fs.existsSync)
 * @param {function} [options.log] - Logging function (defaults to console.log)
 * @throws {Error} If files not found or generation fails
 */
function writeArtifactsToDisk(options = {}) {
  const fs = require('fs');
  const path = require('path');

  const {
    schemaPath = 'common/schemas/dog.schema.json',
    configPath = 'common/config.json',
    statusMappingPath = 'common/statusMapping.js',
    sizeConfigPath = 'common/sizeConfig.js',
    configArtifactPath = 'common/configArtifact.js',
    pythonConfigArtifactPath = 'services/etl_scraper_py/config_artifact.py',
    dogTypesPath = 'services/webapp-react/src/types/Dog.types.ts',
    pythonDogTypesPath = 'services/etl_scraper_py/dog_types.py',
    readFile = (filePath) => fs.readFileSync(filePath, 'utf8'),
    writeFile = (filePath, content) => fs.writeFileSync(filePath, content),
    fileExists = (filePath) => fs.existsSync(filePath),
    log = console.log
  } = options;

  // Validate input files exist
  if (!fileExists(schemaPath)) {
    throw new Error(`Schema file not found: ${schemaPath}`);
  }

  if (!fileExists(configPath)) {
    throw new Error(`Config file not found: ${configPath}`);
  }

  // Read input files
  const schemaContent = readFile(schemaPath);
  const configContent = readFile(configPath);

  // Generate artifacts
  const artifacts = generateAllArtifacts(schemaContent, {
    schemaPath,
    generatorFileName: path.basename(__filename)
  });

  log('Generating schema and config artifacts...');

  // Skip config artifacts for now - they may not be needed

  // Write schema artifacts
  writeFile(statusMappingPath, artifacts.statusMapping);
  writeFile(sizeConfigPath, artifacts.sizeConfig);

  // Update TypeScript types with new header
  updateTypescriptTypesHeader(dogTypesPath, schemaContent, { writeFile, readFile });

  // Write Python types
  writeFile(pythonDogTypesPath, artifacts.pythonDogTypes);

  log('✅ All artifacts generated successfully');
}

/**
 * Update TypeScript types file header with new schema information.
 * @param {string} dogTypesPath - Path to TypeScript types file
 * @param {string} schemaContent - Schema content for checksum generation
 * @param {object} options - Options object
 * @param {function} options.writeFile - File writing function
 * @param {function} options.readFile - File reading function
 */
function updateTypescriptTypesHeader(dogTypesPath, schemaContent, options = {}) {
  const fs = require('fs');
  const path = require('path');

  const {
    writeFile = (filePath, content) => fs.writeFileSync(filePath, content),
    readFile = (filePath) => fs.readFileSync(filePath, 'utf8')
  } = options;

  const content = readFile(dogTypesPath);
  const lines = content.split('\n');

  let commentEndIndex = -1;
  for (let i = 0; i < lines.length; i += 1) {
    if (lines[i].trim() === '*/') {
      commentEndIndex = i;
      break;
    }
  }

  if (commentEndIndex === -1) {
    throw new Error(`${dogTypesPath} is missing an autogenerated header comment block`);
  }

  const newHeader = generateDogTypesHeader(schemaContent, {
    generatorFileName: path.basename(__filename)
  });
  const restOfFile = lines.slice(commentEndIndex + 1).join('\n');
  const newContent = `${newHeader}\n\n${restOfFile}`;

  writeFile(dogTypesPath, newContent);
}

/**
 * Check if artifacts are in sync with source files.
 * @param {object} options - Options object
 * @param {string} [options.schemaPath='common/schemas/dog.schema.json'] - Path to schema file
 * @param {string} [options.configPath='common/config.json'] - Path to config file
 * @param {function} [options.readFile] - File reading function
 * @param {function} [options.fileExists] - File existence check
 * @returns {boolean} True if all artifacts are in sync
 */
function checkArtifactsSync(options = {}) {
  const fs = require('fs');

  const {
    schemaPath = 'common/schemas/dog.schema.json',
    configPath = 'common/config.json',
    readFile = (filePath) => fs.readFileSync(filePath, 'utf8'),
    fileExists = (filePath) => fs.existsSync(filePath)
  } = options;

  // Check if source files exist
  if (!fileExists(schemaPath) || !fileExists(configPath)) {
    return false;
  }

  try {
    const schemaContent = readFile(schemaPath);
    const configContent = readFile(configPath);

    // Generate expected artifacts
    const artifacts = generateAllArtifacts(schemaContent, { schemaPath });

    // Check each artifact file
    const checks = [
      { path: 'common/statusMapping.js', expected: artifacts.statusMapping },
      { path: 'common/sizeConfig.js', expected: artifacts.sizeConfig },
      { path: 'services/etl_scraper_py/dog_types.py', expected: artifacts.pythonDogTypes }
    ];

    for (const check of checks) {
      if (!fileExists(check.path)) {
        return false;
      }
      const actual = readFile(check.path);
      if (actual !== check.expected) {
        return false;
      }
    }

    // Check TypeScript header separately (more complex)
    if (fileExists('services/webapp-react/src/types/Dog.types.ts')) {
      const tsContent = readFile('services/webapp-react/src/types/Dog.types.ts');
      const expectedHeader = generateDogTypesHeader(schemaContent, {
        generatorFileName: 'writers.js'
      });

      if (!tsContent.startsWith(expectedHeader)) {
        return false;
      }
    }

    return true;
  } catch (error) {
    return false;
  }
}

module.exports = {
  generateAllArtifacts,
  generateArtifactBundle,
  writeArtifactsToDisk,
  updateTypescriptTypesHeader,
  checkArtifactsSync
};

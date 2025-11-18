/**
 * Schema artifact writers and orchestration.
 * High-level functions for generating and bundling artifacts.
 */

const { assertSchemaStructure, generateSchemaChecksum, enumerateStatuses, enumerateSizes, enumerateRequiredFields, enumerateFieldOwnership, enumerateTerminalStatuses, getSizeOrdering, extractSchemaMetadata } = require('./loadConfig');
const { generateStatusMapping, generateSizeConfig, generateDogTypesHeader, generatePythonDogTypes, generateConfigArtifact, generatePythonConfigArtifact, generateSchemaArtifact, generatePythonSchemaArtifact } = require('./transformSchema');
const { generateTypescriptDogTypes } = require('./generateTypes');

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
    statusMappingPath = ARTIFACT_PATHS.statusMapping,
    sizeConfigPath = ARTIFACT_PATHS.sizeConfig,
    schemaArtifactPath = ARTIFACT_PATHS.schemaArtifact,
    pythonSchemaArtifactPath = ARTIFACT_PATHS.pythonSchemaArtifact,
    configArtifactPath = ARTIFACT_PATHS.configArtifact,
    pythonConfigArtifactPath = ARTIFACT_PATHS.pythonConfigArtifact,
    dogTypesPath = ARTIFACT_PATHS.dogTypes,
    pythonDogTypesPath = ARTIFACT_PATHS.pythonDogTypes,
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

  // Generate schema artifacts
  const schemaArtifact = generateSchemaArtifact(JSON.parse(schemaContent), schemaContent, {
    generatorFileName: path.basename(__filename)
  });

  // Generate config artifact
  const configArtifact = generateConfigArtifactFromContent(configContent, {
    configPath,
    generatorFileName: path.basename(__filename)
  });

  log('Generating schema and config artifacts...');

  // Write schema artifacts
  writeFile(schemaArtifactPath, schemaArtifact);
  writeFile(statusMappingPath, artifacts.statusMapping);
  writeFile(sizeConfigPath, artifacts.sizeConfig);

  // Write Python schema artifact
  writeFile(pythonSchemaArtifactPath, generatePythonSchemaArtifact(JSON.parse(schemaContent), schemaContent, {
    generatorFileName: path.basename(__filename)
  }));

  // Write config artifacts
  writeFile(configArtifactPath, configArtifact);

  // Write Python config artifact
  writeFile(pythonConfigArtifactPath, generatePythonConfigArtifactFromContent(configContent, {
    configPath,
    generatorFileName: path.basename(__filename)
  }));

  // Write TypeScript types
  writeFile(dogTypesPath, artifacts.typescriptDogTypes);

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

    // Generate schema artifacts
    const schemaArtifact = generateSchemaArtifact(JSON.parse(schemaContent), schemaContent);
    const pythonSchemaArtifact = generatePythonSchemaArtifact(JSON.parse(schemaContent), schemaContent);

    // Generate config artifacts
    const configArtifact = generateConfigArtifactFromContent(configContent, { configPath });
    const pythonConfigArtifact = generatePythonConfigArtifactFromContent(configContent, { configPath });

    // Check each artifact file
    const checks = [
      { path: ARTIFACT_PATHS.schemaArtifact, expected: schemaArtifact },
      { path: ARTIFACT_PATHS.pythonSchemaArtifact, expected: pythonSchemaArtifact },
      { path: ARTIFACT_PATHS.configArtifact, expected: configArtifact },
      { path: ARTIFACT_PATHS.pythonConfigArtifact, expected: pythonConfigArtifact },
      { path: ARTIFACT_PATHS.statusMapping, expected: artifacts.statusMapping },
      { path: ARTIFACT_PATHS.sizeConfig, expected: artifacts.sizeConfig },
      { path: ARTIFACT_PATHS.pythonDogTypes, expected: artifacts.pythonDogTypes }
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
    if (fileExists(ARTIFACT_PATHS.dogTypes)) {
      const tsContent = readFile(ARTIFACT_PATHS.dogTypes);
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
  generateConfigArtifactFromContent,
  generatePythonConfigArtifact,
  writeArtifactsToDisk,
  updateTypescriptTypesHeader,
  checkArtifactsSync
};

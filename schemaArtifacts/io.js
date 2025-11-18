/**
 * Schema artifact I/O operations.
 * File reading, writing, and synchronization functions.
 */

const { ARTIFACT_PATHS } = require('./paths');
const { generateAllArtifacts, generateConfigArtifactFromContent, generatePythonConfigArtifactFromContent } = require('./generators');
const { generateSchemaArtifact, generatePythonSchemaArtifact } = require('./transformSchema');
const { generateDogTypesHeader } = require('./transformSchema');

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
        generatorFileName: 'io.js'
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
  writeArtifactsToDisk,
  updateTypescriptTypesHeader,
  checkArtifactsSync
};

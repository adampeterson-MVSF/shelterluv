/**
 * Thin CLI wrapper for schema artifact generation.
 * Parses arguments and delegates to core functions.
 */

const { writeArtifactsToDisk, checkArtifactsSync } = require('./schemaArtifacts/writers');

/**
 * Parse command line arguments.
 * @param {string[]} argv - Command line arguments
 * @returns {object} Parsed arguments
 */
function parseArgs(argv) {
  const args = argv.slice(2); // Skip node and script name

  if (args.length === 0) {
    return { command: 'generate' };
  }

  const command = args[0];

  if (command === '--help' || command === '-h') {
    return { command: 'help' };
  }

  if (command === '--check-sync' || command === '-c') {
    return { command: 'check-sync' };
  }

  // Default to generate
  return { command: 'generate' };
}

/**
 * Display help text.
 */
function showHelp() {
  console.log(`
Schema Artifact Generator

USAGE:
  node schemaArtifactsCli.js [command]

COMMANDS:
  (no command)    Generate all schema artifacts
  --check-sync    Check if artifacts are in sync with source files
  --help          Show this help message

DESCRIPTION:
  Generates TypeScript types, Python types, status mappings, size configs,
  and other artifacts from the canonical dog schema and configuration.

  All artifacts are generated from:
  - common/schemas/dog.schema.json (schema definitions)
  - common/config.json (configuration)

  Generated files:
  - common/statusMapping.js
  - common/sizeConfig.js
  - common/configArtifact.js
  - services/etl_scraper_py/config_artifact.py
  - services/webapp-react/src/types/Dog.types.ts
  - services/etl_scraper_py/dog_types.py
`);
}

/**
 * Main CLI entry point.
 * @param {string[]} argv - Command line arguments (defaults to process.argv)
 */
function runCli(argv = process.argv) {
  const { command } = parseArgs(argv);

  switch (command) {
    case 'help':
      showHelp();
      process.exit(0);
      break;

    case 'check-sync':
      try {
        const isSynced = checkArtifactsSync();
        if (isSynced) {
          console.log('✅ All artifacts are in sync with source files');
          process.exit(0);
        } else {
          console.log('❌ Artifacts are out of sync with source files');
          console.log('Run without arguments to regenerate artifacts');
          process.exit(1);
        }
      } catch (error) {
        console.error('❌ Error checking sync:', error.message);
        process.exit(1);
      }
      break;

    case 'generate':
    default:
      try {
        writeArtifactsToDisk();
        process.exit(0);
      } catch (error) {
        console.error('❌ Error generating artifacts:', error.message);
        process.exit(1);
      }
      break;
  }
}

// Export for testing and programmatic use
module.exports = {
  parseArgs,
  showHelp,
  runCli,
  writeArtifactsToDisk,
  checkArtifactsSync
};

// Run CLI if called directly
if (require.main === module) {
  runCli();
}


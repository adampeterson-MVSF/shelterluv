#!/usr/bin/env node

/**
 * Firebase CLI Operations Tool
 * Consolidated CLI for Firebase operations and testing.
 *
 * Usage:
 *   node scripts/firebase_cli_tool.js connectivity    # Test CLI connectivity
 *   node scripts/firebase_cli_tool.js persistence     # Run persistence tests
 *   node scripts/firebase_cli_tool.js --help          # Show help
 */

const { parseBasicArgs } = require('./lib/firebaseTools');
const { assertSafeForDestructiveOps } = require('../common/devScriptSafety');
const { getProjectId } = require('../common/firebaseConfig');

const {
  runConnectivityTest,
  runPersistenceTest,
  runAddUser,
  runCheckUsers,
  runCheckData,
  runSeedUsers
} = require('./lib/firebaseCommands');

/**
 * Table-driven command definitions.
 * Each entry defines: name, description, handler, destructive flag, and param requirements.
 */
const COMMANDS = [
  {
    name: 'connectivity',
    description: 'Test Firebase CLI connectivity and basic operations',
    handler: runConnectivityTest,
    destructive: false,
    requiresParams: false
  },
  {
    name: 'persistence',
    description: 'Run data persistence tests (user creation/verification)',
    handler: runPersistenceTest,
    destructive: true,
    requiresParams: false
  },
  {
    name: 'add-user',
    description: 'Add or update a user in Firestore (email uid role [--dry-run] [--domain domain])',
    handler: runAddUser,
    destructive: true,
    requiresParams: true,
    paramCount: 3
  },
  {
    name: 'check-users',
    description: 'Validate user documents in Firestore users collection',
    handler: runCheckUsers,
    destructive: false,
    requiresParams: false
  },
  {
    name: 'check-data',
    description: 'Validate dog documents in Firestore dogs collection',
    handler: runCheckData,
    destructive: false,
    requiresParams: false
  },
  {
    name: 'seed-users',
    description: 'Seed test users with different permission levels',
    handler: runSeedUsers,
    destructive: true,
    requiresParams: false
  }
];

/**
 * Get command definition by name.
 * @param {string} name - Command name
 * @returns {Object|undefined} Command definition
 */
function getCommand(name) {
  return COMMANDS.find(cmd => cmd.name === name);
}

/**
 * Show help information.
 */
function showHelp() {
  console.log('Firebase CLI Operations Tool');
  console.log('Consolidated CLI for Firebase operations and testing.\n');

  console.log('USAGE:');
  console.log('  node scripts/firebase_cli_tool.js <command> [options]\n');

  console.log('COMMANDS:');
  COMMANDS.forEach(cmd => {
    console.log(`  ${cmd.name.padEnd(12)} ${cmd.description}`);
  });

  console.log('\nOPTIONS:');
  console.log('  --help, -h   Show this help message');
  console.log('  --dry-run    Preview operations without making changes');
  console.log('  --verbose    Show detailed output');
  console.log('  --limit N    Limit sample size for data checks (default: 10)');
  console.log('  --reset      Delete and re-seed test users (dangerous!)');
  console.log('  --domain D   Allow emails from specified domain');
}

/**
 * Main entry point.
 */
async function main() {
  const { command, flags, params } = parseBasicArgs(process.argv);

  if (flags.help || flags.h || command === '--help' || command === '-h') {
    showHelp();
    process.exit(0);
  }

  if (!command) {
    console.error('❌ No command specified');
    console.error('Run with --help to see available commands');
    process.exit(1);
  }

  const cmdDef = getCommand(command);
  if (!cmdDef) {
    console.error(`❌ Unknown command: ${command}`);
    console.error('Run with --help to see available commands');
    process.exit(1);
  }

  // Validate parameters for commands that require them
  if (cmdDef.requiresParams && params.length < cmdDef.paramCount) {
    console.error(`Command "${command}" requires ${cmdDef.paramCount} parameters`);
    console.error(`Usage: node scripts/firebase_cli_tool.js ${command} ${'<param> '.repeat(cmdDef.paramCount)}[options]`);
    process.exit(1);
  }

  try {
    let success;
    if (command === 'add-user') {
      // Special handling for add-user which needs params
      success = await cmdDef.handler(params, flags);
    } else {
      success = await cmdDef.handler(flags);
    }
    process.exit(success ? 0 : 1);
  } catch (error) {
    console.error(`❌ Command execution failed: ${error.message}`);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

#!/usr/bin/env node

/**
 * Firebase CLI Operations Tool
 * Thin CLI wrapper around firebase_cli_tool_core.js.
 * Handles argument parsing and delegates to core library.
 *
 * Usage:
 *   node scripts/firebase_cli_tool.js connectivity    # Test CLI connectivity
 *   node scripts/firebase_cli_tool.js persistence     # Run persistence tests
 *   node scripts/firebase_cli_tool.js --help          # Show help
 */

const { parseBasicArgs, getCommands } = require('./firebase_cli_tool_core');

/**
 * Show help information.
 */
function showHelp() {
  console.log('Firebase CLI Operations Tool');
  console.log('Consolidated CLI for Firebase operations and testing.\n');

  console.log('USAGE:');
  console.log('  node scripts/firebase_cli_tool.js <command> [options]\n');

  console.log('COMMANDS:');
  const commands = getCommands();
  commands.forEach(cmd => {
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
 * Get command definition by name.
 */
function getCommand(name) {
  const commands = getCommands();
  return commands.find(cmd => cmd.name === name);
}

/**
 * Main entry point - thin wrapper that delegates to core.
 */
async function main() {
  const { command, flags, params } = parseBasicArgs(process.argv);

  if (!command || flags.help || flags.h) {
    showHelp();
    process.exit(0);
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
      const core = require('./firebase_cli_tool_core');
      success = await core.runAddUser(params, flags);
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
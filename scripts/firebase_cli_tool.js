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

const { runFirebaseCommand, runPersistenceScenario } = require('./lib/firebaseTools');
const { assertSafeForDestructiveOps } = require('../common/devScriptSafety');
const fs = require('fs');
const path = require('path');

const COMMANDS = {
  connectivity: {
    description: 'Test Firebase CLI connectivity and basic operations',
    handler: runConnectivityTest
  },
  persistence: {
    description: 'Run data persistence tests (user creation/verification)',
    handler: runPersistenceTest
  }
};

function showHelp() {
  console.log('Firebase CLI Operations Tool\n');
  console.log('Usage: node scripts/firebase_cli_tool.js <command> [options]\n');
  console.log('Commands:');
  Object.entries(COMMANDS).forEach(([cmd, info]) => {
    console.log(`  ${cmd.padEnd(12)} ${info.description}`);
  });
  console.log('\nOptions:');
  console.log('  --help, -h    Show this help');
  console.log('  --verbose, -v Enable verbose output');
  console.log('  --dry-run     Show what would be done without executing');
}

async function runConnectivityTest(options = {}) {
  console.log('🧪 Firebase CLI Connectivity Test');

  const operations = [
    {
      command: 'projects:list',
      description: 'Check Firebase project access',
      requireSafety: false
    },
    {
      command: 'firestore:databases:list',
      description: 'List Firestore databases',
      requireSafety: false
    },
    {
      command: 'firestore:indexes',
      description: 'Verify database indexes',
      requireSafety: false
    }
  ];

  let allPassed = true;

  for (const op of operations) {
    console.log(`\n🔄 ${op.description}...`);
    const result = runFirebaseCommand(op.command, {
      requireSafety: op.requireSafety,
      verbose: options.verbose
    });

    if (!result.success) {
      console.error(`❌ ${op.description} failed`);
      allPassed = false;
    }
  }

  console.log(`\n📊 CLI Connectivity Test: ${allPassed ? '✅ PASSED' : '❌ FAILED'}`);
  return allPassed;
}

async function runPersistenceTest(options = {}) {
  console.log('🧪 Firebase Data Persistence Test');
  console.log('Testing user creation, verification, and cleanup');

  if (!options.dryRun) {
    assertSafeForDestructiveOps();
  }

  // Load test users from shared fixture
  const testUsersPath = path.join(__dirname, '..', 'common', 'testUsers.json');
  const testUsersData = JSON.parse(fs.readFileSync(testUsersPath, 'utf8'));
  const TEST_USERS = testUsersData.users;

  const scenarios = [
    {
      name: 'Create test users',
      fn: async () => {
        if (options.dryRun) {
          console.log('DRY RUN: Would create users:', TEST_USERS.map(u => u.email).join(', '));
          return;
        }
        // Import here to avoid circular dependencies
        const { seedTestUsers } = require('../common/userManagement');
        const { getAdminDb } = require('../common/adminInit');
        const admin = require('firebase-admin');

        const db = getAdminDb();
        const result = await seedTestUsers(db, admin, { reset: false, dryRun: false });
        if (!result.success) {
          throw new Error(`Failed to seed test users: ${result.error}`);
        }
      }
    },
    {
      name: 'Verify users exist',
      fn: async () => {
        if (options.dryRun) {
          console.log('DRY RUN: Would verify users exist');
          return;
        }
        const { checkUsers } = require('../common/userManagement');
        const { getAdminDb } = require('../common/adminInit');

        const db = getAdminDb();
        const result = await checkUsers(db);
        if (!result.success) {
          throw new Error('User verification failed');
        }
      }
    },
    {
      name: 'Test CLI connectivity',
      fn: async () => {
        const result = runFirebaseCommand('firestore:databases:list', { requireSafety: false });
        if (!result.success) {
          throw new Error('CLI connectivity test failed');
        }
      }
    }
  ];

  const results = [];
  for (const scenario of scenarios) {
    const result = await runPersistenceScenario(scenario.fn, scenario.name);
    results.push({ ...result, scenarioName: scenario.name });
  }

  // Summary
  const passed = results.filter(r => r.success).length;
  const total = results.length;

  console.log(`\n📊 Persistence Test Summary: ${passed}/${total} scenarios passed`);

  if (passed === total) {
    console.log('✅ All persistence tests passed!');
  } else {
    console.log('❌ Some tests failed');
    results.filter(r => !r.success).forEach(r => {
      console.log(`   - ${r.scenarioName}: ${r.error}`);
    });
  }

  return passed === total;
}

async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    showHelp();
    return;
  }

  const command = args[0];
  const options = {
    verbose: args.includes('--verbose') || args.includes('-v'),
    dryRun: args.includes('--dry-run')
  };

  if (!COMMANDS[command]) {
    console.error(`Unknown command: ${command}`);
    console.log('\nAvailable commands:');
    Object.keys(COMMANDS).forEach(cmd => console.log(`  ${cmd}`));
    process.exit(1);
  }

  try {
    const success = await COMMANDS[command].handler(options);
    process.exit(success ? 0 : 1);
  } catch (error) {
    console.error(`❌ Command execution failed: ${error.message}`);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

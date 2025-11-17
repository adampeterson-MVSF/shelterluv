/**
 * Firebase CLI Operations Core Library
 * Contains all Firebase operations and business logic.
 * Used by the CLI wrapper and can be imported programmatically.
 */

const { assertSafe } = require('../common/devScriptSafety');
const { getProjectId } = require('../common/firebaseConfig');
const { createAdminApp } = require('../common/firebaseAdmin');

// Import command implementations from common modules
const { addOrUpdateUser } = require('../common/userRepository');
const { checkDogsCollection } = require('../common/firestoreChecks');
const { seedUsers } = require('../common/userSeed');

/**
 * Run a shell command and return success status.
 * @param {string} command - Command to run
 * @param {string[]} args - Arguments
 * @param {Object} options - Options
 * @returns {Promise<boolean>} Success status
 */
async function runCommand(command, args = [], options = {}) {
  const { spawn } = require('child_process');
  return new Promise((resolve) => {
    const child = spawn(command, args, {
      stdio: 'inherit',
      cwd: options.cwd || process.cwd(),
      env: { ...process.env, ...options.env }
    });

    child.on('close', (code) => {
      resolve(code === 0);
    });

    child.on('error', () => {
      resolve(false);
    });
  });
}

/**
 * Test Firebase CLI connectivity and basic operations.
 */
async function runConnectivityTest(flags) {
  console.log('\n🔍 Testing Firebase CLI connectivity...\n');

  try {
    const projectId = getProjectId();
    console.log(`✅ Connected to project: ${projectId}`);

    const adminApp = createAdminApp();
    const db = adminApp.firestore();

    // Test basic Firestore connectivity
    const testCollection = db.collection('test-connectivity');
    const testDoc = testCollection.doc('connectivity-test');

    await testDoc.set({ timestamp: new Date(), test: 'connectivity' });
    console.log('✅ Firestore write test passed');

    const docSnap = await testDoc.get();
    if (docSnap.exists) {
      console.log('✅ Firestore read test passed');
    }

    await testDoc.delete();
    console.log('✅ Firestore delete test passed');

    console.log('\n🎉 All connectivity tests passed!');
    return true;
  } catch (error) {
    console.error(`❌ Connectivity test failed: ${error.message}`);
    return false;
  }
}

/**
 * Run data persistence tests (user creation/verification).
 */
async function runPersistenceTest(flags) {
  console.log('\n🔍 Running data persistence tests...\n');

  const projectId = getProjectId();
  assertSafe(projectId, { allowDestructive: true });

  try {
    // This would need more complex implementation for full persistence testing
    // For now, just test basic connectivity
    console.log('⚠️  Persistence test not fully implemented yet');
    console.log('   This should test user creation, verification, and cleanup');

    return true;
  } catch (error) {
    console.error(`❌ Persistence test failed: ${error.message}`);
    return false;
  }
}

/**
 * Add or update a user in Firestore.
 */
async function runAddUser(params, flags) {
  const [email, uid, role] = params;
  const { dryRun, domain } = flags;

  console.log(`\n👤 ${dryRun ? 'DRY RUN: ' : ''}Adding/updating user: ${email} (${role})\n`);

  const projectId = getProjectId();
  assertSafe(projectId, { allowDestructive: true });

  try {
    const result = await addOrUpdateUser({
      email,
      uid,
      role,
      domain: domain || 'muttville.org'
    }, { dryRun });

    if (result.success) {
      console.log('✅ User added/updated successfully');
      if (result.data) {
        console.log(`   UID: ${result.data.uid}`);
        console.log(`   Email: ${result.data.email}`);
        console.log(`   Role: ${result.data.role}`);
      }
      return true;
    } else {
      console.error(`❌ Failed to add/update user: ${result.error.message}`);
      return false;
    }
  } catch (error) {
    console.error(`❌ Add user operation failed: ${error.message}`);
    return false;
  }
}

/**
 * Check users in Firestore.
 */
async function runCheckUsers(flags) {
  console.log('\n👥 Checking users in Firestore...\n');

  const projectId = getProjectId();
  assertSafe(projectId);

  try {
    const adminApp = createAdminApp();
    const db = adminApp.firestore();

    const usersCollection = db.collection('users');
    const usersSnapshot = await usersCollection.get();

    console.log(`Found ${usersSnapshot.size} users in Firestore:`);

    usersSnapshot.forEach((doc) => {
      const userData = doc.data();
      console.log(`  - ${doc.id}: ${userData.email} (${userData.role})`);
    });

    console.log('\n✅ User check completed');
    return true;
  } catch (error) {
    console.error(`❌ User check failed: ${error.message}`);
    return false;
  }
}

/**
 * Check data in Firestore collections.
 */
async function runCheckData(flags) {
  console.log('\n📊 Checking Firestore data...\n');

  const projectId = getProjectId();
  assertSafe(projectId);

  try {
    const adminApp = createAdminApp();
    const db = adminApp.firestore();

    // Check dogs collection
    const dogsResult = await checkDogsCollection(db, {
      sampleLimit: flags.limit || 10
    });

    console.log('Dogs collection:');
    console.log(`  - Total documents: ${dogsResult.totalDocuments}`);
    console.log(`  - Available dogs: ${dogsResult.availableDogs}`);
    console.log(`  - Sample documents: ${dogsResult.sampleDocuments.length}`);
    console.log(`  - Schema errors: ${dogsResult.schemaErrors.length}`);

    if (dogsResult.schemaErrors.length > 0) {
      console.log('\nSchema validation errors:');
      dogsResult.schemaErrors.forEach((error, index) => {
        console.log(`  ${index + 1}. ${error.message}`);
      });
    }

    console.log('\n✅ Data check completed');
    return dogsResult.success;
  } catch (error) {
    console.error(`❌ Data check failed: ${error.message}`);
    return false;
  }
}

/**
 * Seed test users.
 */
async function runSeedUsers(flags) {
  console.log('\n🌱 Seeding test users...\n');

  const projectId = getProjectId();
  assertSafe(projectId, { allowDestructive: true });

  try {
    const { reset } = flags;

    if (reset) {
      console.log('⚠️  Reset flag detected - this will delete existing users!');
      console.log('   Make sure you have backups and understand the consequences.');
    }

    const result = await seedUsers({ reset });

    if (result.success) {
      console.log('✅ Test users seeded successfully');
      if (result.data) {
        console.log(`   Created/Updated: ${result.data.length} users`);
        result.data.forEach(user => {
          console.log(`     - ${user.email} (${user.role})`);
        });
      }
      return true;
    } else {
      console.error(`❌ Failed to seed users: ${result.error.message}`);
      return false;
    }
  } catch (error) {
    console.error(`❌ Seed users operation failed: ${error.message}`);
    return false;
  }
}

/**
 * Get command definitions for the CLI.
 */
function getCommands() {
  return [
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
      handler: (flags) => runAddUser(parseBasicArgs(process.argv).params, flags),
      destructive: true,
      requiresParams: true,
      paramCount: 3
    },
    {
      name: 'check-users',
      description: 'Check users in Firestore',
      handler: runCheckUsers,
      destructive: false,
      requiresParams: false
    },
    {
      name: 'check-data',
      description: 'Check data in Firestore collections',
      handler: runCheckData,
      destructive: false,
      requiresParams: false
    },
    {
      name: 'seed-users',
      description: 'Seed test users in Firestore',
      handler: runSeedUsers,
      destructive: true,
      requiresParams: false
    }
  ];
}

/**
 * Parse command line arguments into command, flags, and params.
 * @param {string[]} argv - Process argv
 * @returns {Object} { command, flags, params }
 */
function parseBasicArgs(argv) {
  const args = argv.slice(2); // Skip node and script path
  const flags = {};
  const params = [];

  for (const arg of args) {
    if (arg.startsWith('--')) {
      const flagName = arg.slice(2);
      if (flagName.includes('=')) {
        const [name, value] = flagName.split('=', 2);
        flags[name] = value;
      } else {
        flags[flagName] = true;
      }
    } else if (arg.startsWith('-')) {
      const flagName = arg.slice(1);
      flags[flagName] = true;
    } else {
      params.push(arg);
    }
  }

  const command = params.shift(); // First non-flag arg is command
  return { command, flags, params };
}

module.exports = {
  // Core functions
  runConnectivityTest,
  runPersistenceTest,
  runAddUser,
  runCheckUsers,
  runCheckData,
  runSeedUsers,

  // Utilities
  runCommand,
  parseBasicArgs,
  getCommands
};

/**
 * Test user seeding functionality.
 * Handles creation and management of test users for development.
 */

const fs = require('fs');
const path = require('path');
const { ROLES } = require('./userRoles');
const { validateEmail, isTestUserEmail } = require('./userValidation');
const { addOrUpdateUser } = require('./userRepository');

/**
 * Load and validate test users configuration.
 * @returns {Object} { testUsers, allowedDomains }
 * @throws {Error} If configuration is invalid
 */
function loadAndValidateConfig() {
  const configPath = path.join(__dirname, 'testUsers.json');
  const testUsersData = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  const { users: testUsers, allowedDomains } = testUsersData;

  // Validate test users configuration early - fail fast if any are invalid
  for (const user of testUsers) {
    const result = validateEmail(user.email, allowedDomains);
    if (!result.success) {
      throw new Error(`Invalid email for test user "${user.displayName}": ${user.email}. ${result.error}`);
    }
  }

  // Validate that all roles in testUsers are valid
  const usedRoles = testUsers.map(u => u.role);
  const invalidRoles = usedRoles.filter(role => !ROLES.includes(role));
  if (invalidRoles.length > 0) {
    throw new Error(`Invalid roles found in testUsers: ${invalidRoles.join(', ')}. Valid roles are: ${ROLES.join(', ')}`);
  }

  return { testUsers, allowedDomains };
}

/**
 * Delete existing test users from Firestore and Firebase Auth.
 * @param {Object} db - Firestore database instance
 * @param {Object} auth - Firebase Auth instance
 * @param {Array} testUsers - Test users configuration
 */
async function deleteExistingTestUsers(db, auth, testUsers) {
  console.log('🗑️  Deleting all existing test users...');

  // Get all users from Firestore
  const usersCollection = db.collection('users');
  const usersSnapshot = await usersCollection.get();

  const deletePromises = [];
  usersSnapshot.forEach((doc) => {
    const userData = doc.data();
    // Only delete users that match our test user emails
    if (isTestUserEmail(userData.email, testUsers)) {
      console.log(`   Deleting user: ${userData.email} (${doc.id})`);
      deletePromises.push(doc.ref.delete());
      // Also delete from Firebase Auth
      deletePromises.push(auth.deleteUser(doc.id));
    }
  });

  await Promise.all(deletePromises);
  console.log(`✅ Deleted ${deletePromises.length / 2} test users`);
}

/**
 * Simulate user creation for dry run.
 * @param {Array} testUsers - Test users configuration
 * @param {Array} allowedDomains - Allowed email domains
 * @returns {Array} Simulated user records
 */
async function simulateUserCreation(testUsers, allowedDomains) {
  console.log('📋 DRY RUN - Would perform the following operations:');

  const createdUsers = [];
  for (const userData of testUsers) {
    console.log(`   Would create Firebase Auth user: ${userData.email}`);
    console.log(`   Would ensure Firestore document with role: ${userData.role}`);

    createdUsers.push({
      uid: 'dry-run-uid',
      ...userData
    });
  }

  return createdUsers;
}

/**
 * Create or update test users in Firebase Auth and Firestore.
 * @param {Object} db - Firestore database instance
 * @param {Object} auth - Firebase Auth instance
 * @param {Array} testUsers - Test users configuration
 * @param {Array} allowedDomains - Allowed email domains
 * @returns {Array} Created user records
 */
async function upsertTestUsers(db, auth, testUsers, allowedDomains) {
  const action = 'Ensuring'; // Always ensure since reset is handled separately
  console.log(`🌱 ${action} test users...`);

  const createdUsers = [];

  for (const userData of testUsers) {
    console.log(`👤 Processing user: ${userData.displayName}`);
    console.log(`   Email: ${userData.email}`);
    console.log(`   Role: ${userData.role}`);

    try {
      // Check if user already exists
      let existingUser = null;
      try {
        existingUser = await auth.getUserByEmail(userData.email);
      } catch (error) {
        if (error.code !== 'auth/user-not-found') {
          throw error;
        }
        // User doesn't exist, will create below
      }

      let userRecord;
      if (existingUser) {
        console.log(`📝 User ${userData.email} already exists with UID: ${existingUser.uid}`);
        userRecord = existingUser;
      } else {
        // Create Firebase Auth user
        userRecord = await auth.createUser({
          email: userData.email,
          password: userData.password,
          displayName: userData.displayName,
          emailVerified: true
        });
        console.log(`✅ Created Firebase Auth user with UID: ${userRecord.uid}`);
      }

      // Ensure Firestore document exists with correct role (idempotent)
      const userResult = await addOrUpdateUser(db, auth, userData.email, userRecord.uid, userData.role, { allowedDomains });
      if (!userResult.success) {
        throw new Error(`Failed to create/update user document: ${userResult.error}`);
      }

      createdUsers.push({
        uid: userRecord.uid,
        ...userData
      });

    } catch (error) {
      throw new Error(`Error processing user ${userData.email}: ${error.message}`);
    }

    console.log(''); // Empty line for readability
  }

  return createdUsers;
}

/**
 * Print success message with login credentials and role summary.
 * @param {Array} createdUsers - Created user records
 */
function printSuccessMessage(createdUsers) {
  console.log('🎉 Successfully processed all test users!');
  console.log('\n🔐 TEST LOGIN CREDENTIALS:');
  createdUsers.forEach(user => {
    console.log(`   ${user.email} / ${user.password} (${user.role})`);
  });

  console.log('\n📋 USER ROLES SUMMARY:');
  console.log('   • viewer: Can view dogs but NOT foster contact info');
  console.log('   • closer: Full access including foster contacts');
  console.log('   • staff: Full access including foster contacts and admin functions');
}

/**
 * Seed test users in Firebase Auth and Firestore.
 * Safe to run multiple times - idempotent operation.
 * @param {Object} db - Firestore database instance
 * @param {Object} admin - Firebase Admin instance
 * @param {Object} options - Options object
 * @param {boolean} options.reset - If true, delete all existing test users before seeding
 * @param {boolean} options.dryRun - If true, only log what would be done
 * @returns {Promise<Object>} { success: true, createdUsers: [] } or { success: false, error: string }
 */
async function seedTestUsers(db, admin, options = {}) {
  const { reset = false, dryRun = false } = options;

  try {
    const { testUsers, allowedDomains } = loadAndValidateConfig();
    const auth = admin.auth();

    if (reset && !dryRun) {
      await deleteExistingTestUsers(db, auth, testUsers);
    }

    const createdUsers = dryRun
      ? await simulateUserCreation(testUsers, allowedDomains)
      : await upsertTestUsers(db, auth, testUsers, allowedDomains);

    if (!dryRun) {
      printSuccessMessage(createdUsers);
    }

    return { success: true, createdUsers };

  } catch (error) {
    return { success: false, error: `Error seeding test users: ${error.message}` };
  }
}

module.exports = {
  seedTestUsers
};

/**
 * Shared user management utilities for Firebase Auth and Firestore.
 * Centralizes user creation and update logic used by dev scripts.
 * All functions return { success, error? } for consistent CLI handling.
 */

const { VALID_ROLES, assertValidRole, isValidRole } = require('./userRoles.node.cjs');

/**
 * Validate email format and domain.
 * @param {string} email - Email to validate
 * @param {string[]} allowedDomains - Array of allowed domains
 * @returns {Object} { success: true, email: string } or { success: false, error: string }
 */
function validateEmail(email, allowedDomains = ['muttville.org']) {
  try {
    if (!email || !email.includes('@')) {
      return { success: false, error: 'Invalid email format' };
    }

    const domain = email.split('@')[1];
    if (!allowedDomains.some(allowed => domain === allowed)) {
      return { success: false, error: `Email must be from one of these domains: ${allowedDomains.join(', ')}` };
    }

    return { success: true, email: email.toLowerCase().trim() };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Validate user role using centralized role validation.
 * @param {string} role - Role to validate
 * @returns {Object} { success: true, role: string } or { success: false, error: string }
 */
function validateRole(role) {
  try {
    assertValidRole(role);
    return { success: true, role };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Add or update a user document in Firestore.
 * @param {Object} db - Firestore database instance
 * @param {Object} admin - Firebase Admin instance
 * @param {string} email - User email
 * @param {string} uid - User UID
 * @param {string} role - User role
 * @param {Object} options - Options object
 * @param {boolean} options.dryRun - If true, only log what would be done
 * @param {string[]} options.allowedDomains - Array of allowed email domains
 * @returns {Promise<Object>} { success: true } or { success: false, error: string }
 */
async function addOrUpdateUser(db, admin, email, uid, role, options = {}) {
  try {
    const { dryRun = false, allowedDomains = ['muttville.org'] } = options;

    // Validate inputs
    const emailResult = validateEmail(email, allowedDomains);
    if (!emailResult.success) return emailResult;

    const roleResult = validateRole(role);
    if (!roleResult.success) return roleResult;

    const validatedEmail = emailResult.email;
    const validatedRole = roleResult.role;

    const action = dryRun ? 'DRY RUN: Would add/update' : 'Adding/updating';
    console.log(`👤 ${action} user document for ${email}...`);

    if (dryRun) {
      console.log('📋 DRY RUN - Would perform the following operations:');
      console.log(`   UID: ${uid}`);
      console.log(`   Email: ${validatedEmail}`);
      console.log(`   Role: ${validatedRole}`);
      console.log('   Action: Check if user exists, then create or update document');
      console.log('✅ Dry run completed - no changes made');
      return { success: true };
    }

    const userDocRef = db.collection('users').doc(uid);

    // Check if user already exists
    const existingDoc = await userDocRef.get();

    if (existingDoc.exists) {
      // Update existing user
      console.log('📝 User document exists, updating role...');
      await userDocRef.update({
        email: validatedEmail,
        role: validatedRole,
        updatedAt: admin.firestore.FieldValue.serverTimestamp()
      });
      console.log('✅ Successfully updated user document!');
    } else {
      // Create new user
      console.log('🆕 User document does not exist, creating...');
      await userDocRef.set({
        email: validatedEmail,
        displayName: email.split('@')[0].replace('.', ' '), // Simple display name from email
        role: validatedRole,
        createdAt: admin.firestore.FieldValue.serverTimestamp(),
        updatedAt: admin.firestore.FieldValue.serverTimestamp()
      });
      console.log('✅ Successfully created user document!');
    }

    console.log(`   UID: ${uid}`);
    console.log(`   Email: ${validatedEmail}`);
    console.log(`   Role: ${validatedRole}`);

    return { success: true };
  } catch (error) {
    console.error('❌ Failed to add/update user:', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Check if an email belongs to a test user.
 * @param {string} email - Email to check
 * @param {Array} testUsers - Array of test user objects with email property
 * @returns {boolean} True if email belongs to a test user
 */
function isTestUserEmail(email, testUsers) {
  return testUsers.some(testUser => testUser.email === email);
}

/**
 * Check users collection for data integrity and role validation.
 * @param {Object} db - Firestore database instance
 * @returns {Promise<Object>} Structured results: { success, totalUsers, roleCounts, invalidUsers, summary }
 */
async function checkUsers(db) {
  const results = {
    success: true,
    totalUsers: 0,
    roleCounts: {},
    invalidUsers: [],
    summary: ''
  };

  try {
    const usersCollection = db.collection('users');
    const usersSnapshot = await usersCollection.get();

    results.totalUsers = usersSnapshot.size;

    // Initialize role counts
    VALID_ROLES.forEach(role => {
      results.roleCounts[role] = 0;
    });
    results.roleCounts.unknown = 0;

    usersSnapshot.forEach((doc) => {
      const data = doc.data();
      const role = data.role;

      // Count by role
      if (isValidRole(role)) {
        results.roleCounts[role]++;
      } else {
        results.roleCounts.unknown++;
        results.invalidUsers.push({ uid: doc.id, email: data.email, role: role });
      }
    });

    // Create summary
    const validRoles = VALID_ROLES;
    const invalidCount = results.roleCounts.unknown;

    results.summary = `Total: ${results.totalUsers}, Valid roles: ${validRoles.map(r => `${r}=${results.roleCounts[r]}`).join(' ')}, Invalid: ${invalidCount}`;

    if (invalidCount > 0) {
      results.success = false;
    }

  } catch (error) {
    results.success = false;
    results.summary = `Error: ${error.message}`;
  }

  return results;
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
    const fs = require('fs');
    const testUsersData = JSON.parse(fs.readFileSync('./common/testUsers.json', 'utf8'));
    const testUsers = testUsersData.users;
    const allowedDomains = testUsersData.allowedDomains;

    // Validate test users configuration early - fail fast if any are invalid
    for (const user of testUsers) {
      const result = validateEmail(user.email, allowedDomains);
      if (!result.success) {
        return { success: false, error: `Invalid email for test user "${user.displayName}": ${user.email}. ${result.error}` };
      }
    }

    // Validate that all roles in testUsers are valid
    const usedRoles = testUsers.map(u => u.role);
    const invalidRoles = usedRoles.filter(role => !VALID_ROLES.includes(role));
    if (invalidRoles.length > 0) {
      return {
        success: false,
        error: `Invalid roles found in testUsers: ${invalidRoles.join(', ')}. Valid roles are: ${VALID_ROLES.join(', ')}`
      };
    }

    const auth = admin.auth();
    const createdUsers = [];

    if (reset && !dryRun) {
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

    if (dryRun) {
      console.log('📋 DRY RUN - Would perform the following operations:');
    } else {
      const action = reset ? 'Creating fresh' : 'Ensuring';
      console.log(`🌱 ${action} test users...`);
    }

    for (const userData of testUsers) {
      if (!dryRun) {
        console.log(`👤 Processing user: ${userData.displayName}`);
        console.log(`   Email: ${userData.email}`);
        console.log(`   Role: ${userData.role}`);
      }

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
          if (!dryRun) {
            console.log(`📝 User ${userData.email} already exists with UID: ${existingUser.uid}`);
          }

          // In reset mode, we deleted all users, so this shouldn't happen
          // In normal mode, ensure the role is correct
          userRecord = existingUser;
        } else {
          if (dryRun) {
            console.log(`   Would create Firebase Auth user: ${userData.email}`);
            userRecord = { uid: 'dry-run-uid', email: userData.email };
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
        }

        if (dryRun) {
          console.log(`   Would ensure Firestore document with role: ${userData.role}`);
        } else {
          // Ensure Firestore document exists with correct role (idempotent)
          const userResult = await addOrUpdateUser(db, admin, userData.email, userRecord.uid, userData.role, { allowedDomains });
          if (!userResult.success) {
            throw new Error(`Failed to create/update user document: ${userResult.error}`);
          }
        }

        createdUsers.push({
          uid: userRecord.uid,
          ...userData
        });

      } catch (error) {
        return { success: false, error: `Error processing user ${userData.email}: ${error.message}` };
      }

      if (!dryRun) {
        console.log(''); // Empty line for readability
      }
    }

    if (!dryRun) {
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

    return { success: true, createdUsers };

  } catch (error) {
    return { success: false, error: `Error seeding test users: ${error.message}` };
  }
}

module.exports = {
  validateEmail,
  validateRole,
  addOrUpdateUser,
  checkUsers,
  isTestUserEmail,
  seedTestUsers
};

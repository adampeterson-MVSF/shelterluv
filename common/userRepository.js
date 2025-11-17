/**
 * User repository for Firestore and Firebase Auth operations.
 * Contains all I/O operations for user management.
 */

const { VALID_ROLES, isValidRole } = require('./userRoles');
const userValidation = require('./userValidation');
const validateEmail = userValidation.validateEmail;
const validateRole = userValidation.validateRole;

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
 * Generate machine-readable JSON output of user check results.
 * @param {Object} results - Results from checkUsers
 * @returns {string} JSON string
 */
function formatUsersJson(results) {
  // Create a clean object without the summary string
  const jsonResult = {
    success: results.success,
    totalUsers: results.totalUsers,
    roleCounts: results.roleCounts,
    invalidUsers: results.invalidUsers
  };

  // Add error info if present
  if (!results.success && results.summary && results.summary.startsWith('Error:')) {
    jsonResult.error = results.summary.slice(7); // Remove "Error: " prefix
  }

  return JSON.stringify(jsonResult, null, 2);
}

module.exports = {
  addOrUpdateUser,
  checkUsers,
  formatUsersJson
};

/**
 * ⚠️  DEV-ONLY SCRIPT: Add/Update User in Firestore ⚠️
 *
 * This script adds or updates a user document in the Firestore users collection.
 * ONLY USE IN DEVELOPMENT/TESTING ENVIRONMENTS.
 *
 * Usage: node add_user.js <email> <uid> <role> [--dry-run] [--domain <domain>]
 * Example: node add_user.js adam.peterson@muttville.org 4b3t0J7GGCZMhZv628CMHz8Xwqb2 staff
 * Example: node add_user.js adam.peterson@muttville.org 4b3t0J7GGCZMhZv628CMHz8Xwqb2 staff --dry-run
 * Example: node add_user.js test@example.com uid123 viewer --domain example.com
 */

const { getAdminDb } = require('./common/adminInit');
const { assertSafeForDestructiveOps } = require('./common/devScriptSafety');
const { VALID_ROLES } = require('./common/userRoles.node.cjs');
const { validateEmail, validateRole, addOrUpdateUser } = require('./common/userManagement');
const admin = require('firebase-admin');

async function run({ email, uid, role, dryRun, domain }) {
  try {
    // Safety checks
    assertSafeForDestructiveOps();

    // Validate inputs
    const allowedDomains = domain ? [domain] : ['muttville.org'];
    const emailResult = validateEmail(email, allowedDomains);
    if (!emailResult.success) {
      throw new Error(emailResult.error);
    }

    const roleResult = validateRole(role);
    if (!roleResult.success) {
      throw new Error(roleResult.error);
    }

    // Get Firebase Admin DB
    const db = getAdminDb();

    // Add/update user using centralized function
    const result = await addOrUpdateUser(db, admin, emailResult.email, uid, roleResult.role, { dryRun, allowedDomains });
    if (!result.success) {
      throw new Error(result.error);
    }

    return { success: true };
  } catch (error) {
    console.error('❌ Error adding/updating user:', error.message);
    return { success: false, error: error.message };
  }
}

// Parse command line arguments with improved validation
function parseArgs() {
  const args = process.argv.slice(2);

  // Check for help flag first
  if (args.includes('--help') || args.includes('-h')) {
    printUsage();
    process.exit(0);
  }

  const dryRun = args.includes('--dry-run');

  // Find domain flag
  let domain = null;
  const domainIndex = args.indexOf('--domain');
  if (domainIndex !== -1 && domainIndex + 1 < args.length) {
    domain = args[domainIndex + 1];
  }

  // Remove flags from args
  const filteredArgs = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--dry-run') {
      // Skip --dry-run flag
      continue;
    } else if (args[i] === '--domain') {
      // Skip --domain flag and its value
      i++; // Skip the next argument (domain value)
      continue;
    } else {
      // Keep positional arguments
      filteredArgs.push(args[i]);
    }
  }

  if (filteredArgs.length !== 3) {
    printUsage();
    process.exit(1);
  }

  const [email, uid, role] = filteredArgs;
  return { email, uid, role, dryRun, domain };
}

function printUsage() {
  console.log('⚠️  DEV-ONLY SCRIPT: Add/Update User in Firestore ⚠️');
  console.log('');
  console.log('This script adds or updates a user document in the Firestore users collection.');
  console.log('ONLY USE IN DEVELOPMENT/TESTING ENVIRONMENTS.');
  console.log('');
  console.log('Usage: node add_user.js <email> <uid> <role> [options]');
  console.log('');
  console.log('Arguments:');
  console.log('  email    User email address');
  console.log('  uid      Firebase Auth user UID');
  console.log('  role     User role (viewer, closer, staff)');
  console.log('');
  console.log('Options:');
  console.log('  --dry-run    Show what would be done without making changes');
  console.log('  --domain     Allow emails from specified domain (default: muttville.org)');
  console.log('  --help, -h   Show this help message');
  console.log('');
  console.log('Examples:');
  console.log('  node add_user.js adam.peterson@muttville.org 4b3t0J7GGCZMhZv628CMHz8Xwqb2 staff');
  console.log('  node add_user.js adam.peterson@muttville.org 4b3t0J7GGCZMhZv628CMHz8Xwqb2 staff --dry-run');
  console.log('  node add_user.js test@example.com uid123 viewer --domain example.com');
  console.log('');
  console.log('Valid roles:', VALID_ROLES.join(', '));
}

// Export parseArgs for testing
module.exports = { parseArgs };

function main() {
  const args = parseArgs();
  return run(args);
}

if (require.main === module) {
  main().then((result) => {
    if (!result.success) {
      process.exit(1);
    }
  }).catch((error) => {
    console.error('❌ Fatal error:', error.message);
    process.exit(1);
  });
}

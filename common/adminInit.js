/**
 * Shared Firebase Admin SDK initialization for dev scripts and admin tools.
 * Enforces single initialization using centralized config and safety checks.
 */

const admin = require('firebase-admin');
const path = require('path');
const { validateFirebaseAdminEnv, getFirebaseProjectId } = require('./firebaseConfig');
const { assertNotProdProject } = require('./firebaseSafetyConfig');

let initialized = false;

/**
 * Get Firebase Admin database instance, initializing if needed.
 * Enforces single initialization, validates environment, and ensures safe project.
 *
 * @returns {Object} Firestore database instance
 * @throws {Error} If initialization fails or project is unsafe
 */
function getAdminDb() {
  if (initialized) {
    return admin.firestore();
  }

  // Validate environment and get project ID
  validateFirebaseAdminEnv();
  const projectId = getFirebaseProjectId();

  // Safety check
  assertNotProdProject(projectId, 'admin operations');

  // Initialize admin with optional service account path override
  const defaultKeyPath = path.join(__dirname, '..', 'firebase-admin-key.json');
  const serviceAccountPath = process.env.FIREBASE_ADMIN_KEY_PATH || defaultKeyPath;

  try {
    admin.initializeApp({
      credential: admin.credential.cert(serviceAccountPath),
      projectId: projectId
    });
    console.log(`✅ Firebase Admin initialized for project: ${projectId}`);
    initialized = true;
  } catch (error) {
    if (error.code !== 'app/duplicate-app') {
      console.error('❌ Failed to initialize Firebase Admin SDK:', error.message);
      throw error;
    }
    initialized = true; // App was already initialized elsewhere
  }

  return admin.firestore();
}

module.exports = {
  getAdminDb
};

/**
 * Shared Firebase Admin SDK initialization for dev scripts and admin tools.
 * Enforces single initialization using centralized config and safety checks.
 */

const admin = require('firebase-admin');
const path = require('path');
const { validateFirebaseEnv, getFirebaseProjectId } = require('./firebaseConfig');
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

  // Validate environment first
  validateFirebaseEnv();

  const projectId = getFirebaseProjectId();
  if (!projectId) {
    throw new Error('FIREBASE_PROJECT_ID environment variable is required');
  }

  // Safety check
  assertNotProdProject(projectId, 'admin operations');

  // Initialize admin
  const serviceAccountPath = path.join(__dirname, '..', 'firebase-admin-key.json');
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

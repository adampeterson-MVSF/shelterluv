/**
 * Firebase Admin SDK initialization and management.
 * Contains all side effects related to Firebase Admin app creation.
 * Enforces singleton pattern to prevent multiple app initializations.
 */

const { ensureProfile, getAdminProjectId } = require('./firebaseConfig');

let adminApp = null;

/**
 * Create and initialize Firebase admin app with validated config.
 * Enforces singleton: returns existing app if already initialized.
 * This is the ONLY place where firebase-admin gets initialized in scripts.
 * @returns {Object} Initialized Firebase admin app
 */
function createAdminApp() {
  if (adminApp) {
    return adminApp;
  }

  ensureProfile('admin');
  const admin = require('firebase-admin');
  const projectId = getAdminProjectId();

  if (!projectId) {
    throw new Error('Project ID is required but was not found in environment');
  }

  adminApp = admin.initializeApp({
    projectId: projectId
  });

  return adminApp;
}

module.exports = {
  createAdminApp
};

// Centralized app initialization - no global Firebase state
import { buildFirebaseConfig, createFirebaseApp, createAuthService } from './services/firebase';

// Build Firebase config with validation - fails fast if env vars missing
const firebaseConfig = buildFirebaseConfig();

// Initialize Firebase services - only done once at app startup
const { app, db, auth } = createFirebaseApp(firebaseConfig);

// Create auth service instance
const authService = createAuthService(auth);

/**
 * Get Firebase services - single entry point for Firebase dependencies.
 * Returns initialized services for use throughout the app.
 * @returns {Object} Firebase services object
 */
export function getFirebaseServices() {
  return { db, authService };
}

// Export initialized services for use throughout the app
export { db, authService };
export default app;

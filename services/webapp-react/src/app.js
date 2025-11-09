// Centralized app initialization - no global Firebase state
import { buildFirebaseConfig, createFirebaseApp, createAuthService } from './services/firebase';

// Build Firebase config with validation - fails fast if env vars missing
const firebaseConfig = buildFirebaseConfig();

// Initialize Firebase services - only done once at app startup
const { app, db, auth } = createFirebaseApp(firebaseConfig);

// Create auth service instance
const authService = createAuthService(auth);

// Export initialized services for use throughout the app
export { db, authService };
export { authService as auth }; // Alias for backward compatibility
export default app;

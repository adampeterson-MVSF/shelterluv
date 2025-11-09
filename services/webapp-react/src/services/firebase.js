// Firebase configuration - centralized, no global initialization
import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';
import { getAuth, GoogleAuthProvider, signInWithPopup, onAuthStateChanged, signOut } from 'firebase/auth';
import { getWebFirebaseConfigFromEnv } from '../../../../common/firebaseConfig.js';

// Webapp-specific environment variable getter (Vite requires VITE_ prefix)
function getViteEnvVar(varName) {
  // In Vite, only VITE_ prefixed vars are available in browser
  const vitePrefixed = import.meta.env[`VITE_${varName}`];

  if (vitePrefixed) return vitePrefixed;

  throw new Error(`Missing required environment variable: VITE_${varName} (Vite requires VITE_ prefix for browser access)`);
}

// Pure function to build Firebase config object using centralized helper
export function buildFirebaseConfig() {
  return getWebFirebaseConfigFromEnv(getViteEnvVar);
}

// Pure function to create Firebase app and services
export function createFirebaseApp(config) {
  const app = initializeApp(config);
  const db = getFirestore(app);
  const auth = getAuth(app);
  return { app, db, auth };
}

// Pure function to create Google Auth Provider with domain hint
export function createGoogleAuthProvider() {
  const provider = new GoogleAuthProvider();
  // Hint at muttville.org domain (note: this is a hint only, not enforcement)
  provider.setCustomParameters({ hd: 'muttville.org' });
  return provider;
}

// Factory function to create auth service with Firebase auth instance
export function createAuthService(auth) {
  const provider = createGoogleAuthProvider();

  return {
    async signInWithGoogle() {
      const result = await signInWithPopup(auth, provider);
      return result.user;
    },

    async signOutUser() {
      return signOut(auth);
    },

    subscribeToAuthChanges(callback) {
      return onAuthStateChanged(auth, callback);
    }
  };
}


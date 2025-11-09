// Test setup - centralized mocks and configuration
import '@testing-library/jest-dom';
import { config } from 'dotenv';
import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load environment variables from .env and .env.local files
// This ensures tests have access to credentials and configuration
config({ path: path.resolve(__dirname, '../../.env') });
config({ path: path.resolve(__dirname, '../../.env.local') });

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock environment variables for Firebase (Vite format with VITE_ prefix)
vi.stubGlobal('import', {
  meta: {
    env: {
      VITE_FIREBASE_API_KEY: 'test-api-key',
      VITE_FIREBASE_AUTH_DOMAIN: 'test.firebaseapp.com',
      VITE_FIREBASE_PROJECT_ID: 'test-project',
      VITE_FIREBASE_STORAGE_BUCKET: 'test.appspot.com',
      VITE_FIREBASE_MESSAGING_SENDER_ID: '123456789',
      VITE_FIREBASE_APP_ID: '1:123456789:web:abcdef123456'
    }
  }
});

// Mock getFirestore to return a mock Firestore instance
vi.mock('firebase/firestore', () => ({
  getFirestore: vi.fn(() => ({
    // Mock Firestore instance methods if needed
  })),
  doc: vi.fn(() => ({
    // Mock document reference
    id: 'mock-doc-id'
  })),
  getDoc: vi.fn(), // Tests will override this
  collection: vi.fn(),
  getDocs: vi.fn(),
  query: vi.fn(),
  where: vi.fn(),
  orderBy: vi.fn(),
  limit: vi.fn(),
  onSnapshot: vi.fn(),
  addDoc: vi.fn(),
  updateDoc: vi.fn(),
  deleteDoc: vi.fn(),
  setDoc: vi.fn(),
}));

// Mock Firebase to prevent initialization errors in tests
vi.mock('firebase/app', () => ({
  initializeApp: vi.fn(() => ({ name: '[DEFAULT]' })),
  getApps: vi.fn(() => []),
  getApp: vi.fn(() => ({ name: '[DEFAULT]' }))
}));

// Mock Firebase service - tests can override these
vi.mock('../services/firebase', () => ({
  buildFirebaseConfig: vi.fn(() => ({
    apiKey: 'test-api-key',
    authDomain: 'test.firebaseapp.com',
    projectId: 'test-project',
    storageBucket: 'test.appspot.com',
    messagingSenderId: '123456789',
    appId: '1:123456789:web:abcdef123456'
  })),
  createFirebaseApp: vi.fn(() => ({
    app: { name: '[DEFAULT]' },
    db: {},
    auth: {}
  })),
  createAuthService: vi.fn(() => ({
    signInWithGoogle: vi.fn().mockResolvedValue({
      uid: 'test-user-123',
      email: 'test@muttville.org',
      displayName: 'Test User',
      emailVerified: true,
    }),
    signOutUser: vi.fn().mockResolvedValue(),
    subscribeToAuthChanges: vi.fn(() => {
      // Return unsubscribe function
      return () => {};
    })
  }))
}));

// Mock app initialization - tests can override these
vi.mock('../app', () => ({
  db: 'mock-db-instance',
  authService: {
    signInWithGoogle: vi.fn().mockResolvedValue({
      uid: 'test-user-123',
      email: 'test@muttville.org',
      displayName: 'Test User',
      emailVerified: true,
    }),
    signOutUser: vi.fn().mockResolvedValue(),
    subscribeToAuthChanges: vi.fn(() => {
      // Return unsubscribe function
      return () => {};
    })
  }
}));

// Mock AuthContext - tests can override specific parts
vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    authState: { kind: 'loading' },
    login: vi.fn().mockResolvedValue({ success: true }),
    logout: vi.fn().mockResolvedValue({ success: true }),
    hasRole: vi.fn(),
    hasAnyRole: vi.fn(),
    isAuthenticated: false
  })),
  AuthProvider: ({ children }) => children // Default: pass through children without provider
}));

vi.mock('firebase/auth', () => ({
  getAuth: vi.fn(() => ({})),
  GoogleAuthProvider: vi.fn().mockImplementation(function() {
    return {
      setCustomParameters: vi.fn(),
    };
  }),
  signInWithPopup: vi.fn().mockResolvedValue({
    user: {
      uid: 'test-user-123',
      email: 'test@muttville.org',
      displayName: 'Test User',
      emailVerified: true,
    },
  }),
  signOut: vi.fn().mockResolvedValue(),
  onAuthStateChanged: vi.fn(() => {
    // Return unsubscribe function
    return () => {};
  }),
}));
